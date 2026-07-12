"""Local file storage for uploaded asset media (photos / documents).

Files live under <project>/media and are served statically at /media/* by the
FastAPI app. We keep a flat directory and derive safe, unique filenames so the
upload endpoint can't be used to traverse the filesystem.
"""
import os
import re
import uuid

# <project_root>/media
MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "media"))

_ALLOWED_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt",
}


def _safe_name(original: str) -> str:
    base, ext = os.path.splitext(original)
    ext = ext.lower()
    if ext not in _ALLOWED_EXT:
        ext = ".bin"
    # Strip path separators / control chars from the user-supplied name.
    clean = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:60]
    token = uuid.uuid4().hex[:12]
    return f"{clean}_{token}{ext}"


def save_upload(filename: str, content: bytes) -> str:
    """Persist `content` and return the public path served at /media/*."""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    safe = _safe_name(filename)
    dest = os.path.join(MEDIA_DIR, safe)
    with open(dest, "wb") as fh:
        fh.write(content)
    return f"/media/{safe}"
