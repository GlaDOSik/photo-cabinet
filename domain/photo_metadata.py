from typing import Dict, Any


class PhotoMetadata:
    """
    Flexible container for *any* metadata.
    - flat:      flat map with "GROUP:Tag" -> value (e.g., "XMP:RegionInfo")
    - by_group:  nested map group -> { tag -> value }
    - path:      absolute file path
    - file_size: bytes (int) if available
    - mime_type: if ExifTool reports it
    """
    path: str
    flat: Dict[str, Any]
    by_group: Dict[str, Dict[str, Any]]
    file_size: int | None = None
    mime_type: str | None = None