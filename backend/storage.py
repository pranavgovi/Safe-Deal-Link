import os
import uuid

from fastapi import UploadFile

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload(file: UploadFile) -> str:
    """Saves an uploaded file to backend/uploads and returns a URL path
    that main.py serves via StaticFiles (e.g. /uploads/<filename>)."""
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    with open(dest_path, "wb") as out:
        out.write(file.file.read())
    return f"/uploads/{filename}"


def local_path_for_url(url: str) -> str:
    """Resolves a /uploads/<filename> URL back to its path on disk."""
    filename = url.rsplit("/", 1)[-1]
    return os.path.join(UPLOAD_DIR, filename)
