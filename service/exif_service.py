from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple, Iterable

from domain.photo_metadata import PhotoMetadata

EXIFTOOL_BIN = shutil.which("exiftool") or "exiftool"

def _run_exiftool(args: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    cmd = [EXIFTOOL_BIN] + args
    try:
        return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except FileNotFoundError:
        sys.exit("Error: exiftool not found. Install it and ensure it’s on PATH.")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(e.stderr.decode(errors="replace"))
        raise
    except subprocess.TimeoutExpired:
        sys.exit("Error: exiftool timed out.")

# ---------- Reading ----------

def read_all_metadata(path: str) -> Dict[str, Any]:
    """
    Returns raw ExifTool JSON for the file, with:
      -G1 (group names), -a (allow duplicate tags), -u (include unknown),
      -n (numeric where applicable), -struct (structured XMP),
      -api largefilesupport=1 (for big files).
    """
    args = [
        "-G1", "-a", "-u", "-n", "-struct",
        "-api", "largefilesupport=1",
        "-j", "--icc_profile:all",          # don't dump binary ICC blobs to keep output sane
        "-charset", "filename=UTF8",
        path,
    ]
    proc = _run_exiftool(args)
    data = json.loads(proc.stdout.decode("utf-8", errors="replace"))
    # ExifTool returns a list (one item per SourceFile)
    return data[0] if data else {}

def _split_group_tag(key: str) -> Tuple[str, str]:
    # ExifTool with -G1 yields keys like "XMP:CreateDate", "EXIF:DateTimeOriginal"
    if ":" in key:
        g, t = key.split(":", 1)
        return g, t
    # Fallback group
    return "Unknown", key

def to_metadata(raw: Dict[str, Any]) -> PhotoMetadata:
    flat: Dict[str, Any] = {}
    by_group: Dict[str, Dict[str, Any]] = {}

    src = raw.get("SourceFile")
    path = os.path.abspath(src) if src else "<unknown>"

    # Collect everything that looks like a tag (skip SourceFile and file stats handled later)
    for k, v in raw.items():
        if k in {"SourceFile"}:
            continue
        g, t = _split_group_tag(k)
        flat_key = f"{g}:{t}"
        flat[flat_key] = v
        by_group.setdefault(g, {})[t] = v

    # Common helpers
    size = None
    for key in ("File:FileSize", "System:FileSize"):
        if key in flat:
            # ExifTool `-n` may return bytes as int/string; try to parse
            try:
                size = int(flat[key])
            except Exception:
                size = None
            break

    mime = None
    for key in ("File:MIMEType", "System:MIMEType"):
        if key in flat:
            mime = flat[key]
            break

    return PhotoMetadata(path=path, flat=flat, by_group=by_group, file_size=size, mime_type=mime)

# ---------- Writing ----------

def _build_set_args(updates: Iterable[Tuple[str, Any]]) -> List[str]:
    """
    Convert (tag, value) into exiftool CLI args.
    Rules:
      - tag must be like "GROUP:Tag" (e.g., "XMP:Label", "IPTC:Keywords", "EXIF:Artist").
      - value is:
          * None -> delete tag (-TAG=)
          * list/tuple -> multiple -TAG=VALUE occurrences
          * otherwise -> -TAG=VALUE
      - We do not force types; ExifTool handles reasonable coercions.
    """
    args: List[str] = []
    for tag, value in updates:
        if not tag or ":" not in tag:
            raise ValueError(f"Tag must include group: 'GROUP:Tag', got '{tag}'")
        if value is None:
            args.append(f"-{tag}=")  # delete
        elif isinstance(value, (list, tuple)):
            for item in value:
                args.append(f"-{tag}={item}")
        else:
            args.append(f"-{tag}={value}")
    return args

def set_metadata(path: str, updates: Dict[str, Any], overwrite_original: bool = False) -> None:
    """
    Set arbitrary tags. Examples:
      set_metadata("img.jpg", {"XMP:Label": "Blue", "IPTC:Keywords": ["a","b"]}, overwrite_original=True)
      set_metadata("img.jpg", {"XMP:Subject": None})  # delete XMP:Subject
    """
    args = [
        "-P",                               # preserve file mtimes when possible
        "-charset", "filename=UTF8",
        "-api", "largefilesupport=1",
        "-m",                               # ignore minor warnings
    ]
    if overwrite_original:
        args.append("-overwrite_original")
    args += _build_set_args(updates.items())
    args.append(path)
    _run_exiftool(args)

# ---------- CLI ----------

def _parse_set_args(argv: List[str]) -> Tuple[Dict[str, Any], bool, List[str]]:
    """
    Parse: --set TAG=VALUE  (may repeat)
           --set TAG=       (delete)
           --overwrite
    """
    updates: Dict[str, Any] = {}
    overwrite = False
    rest: List[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--overwrite":
            overwrite = True
            i += 1
            continue
        if tok == "--set":
            if i + 1 >= len(argv):
                sys.exit("Error: --set requires TAG=VALUE (or TAG= to delete).")
            pair = argv[i + 1]
            i += 2
            if "=" not in pair:
                sys.exit("Error: --set requires TAG=VALUE.")
            tag, val = pair.split("=", 1)
            tag = tag.strip()
            # Empty value => delete
            if val == "":
                updates[tag] = None
            else:
                # Allow multiple values via repeated --set TAG=value (handled by dict last-write wins),
                # or comma-split helper if caller prefers a single arg. Keep it simple:
                if "," in val and tag.lower().endswith(("keywords", "subject", "hierarchicalsubject")):
                    updates[tag] = [x.strip() for x in val.split(",") if x.strip()]
                else:
                    updates[tag] = val
            continue
        rest.append(tok)
        i += 1
    return updates, overwrite, rest