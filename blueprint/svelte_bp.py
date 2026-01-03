# svelte_bp.py
import os
from datetime import timedelta
from flask import Blueprint, send_from_directory
import logging

svelte_bp = Blueprint(
    "svelte",
    __name__
)

SVELTE_STATIC_PATH = "/photo-cabinet/svelte"

@svelte_bp.after_app_request
def add_cache_headers(resp):
    if resp.direct_passthrough and resp.status_code == 200:
        ctype = resp.headers.get("Content-Type", "")
        if any(x in ctype for x in ["javascript", "css", "image", "font"]):
            resp.cache_control.max_age = int(timedelta(days=365).total_seconds())
    return resp

@svelte_bp.route("/", defaults={"path": ""})
@svelte_bp.route("/<path:path>")
def spa(path):
    log = logging.getLogger("sveltebp")
    # Skip API routes - let Flask-Smorest handle them
    log.error(str(path))
    if path.startswith("api/") or path.startswith("openapi.json"):
        return None

    # Check if the requested path exists as a static file
    full = os.path.join(SVELTE_STATIC_PATH, path)
    if path and os.path.exists(full) and os.path.isfile(full):
        return send_from_directory(SVELTE_STATIC_PATH, path)

    # For all other routes (including SPA routes), serve index.html
    return send_from_directory(SVELTE_STATIC_PATH, "index.html")
