"""
app/utils/helpers.py – Reusable helper functions.
"""

import os
import secrets
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file_storage, subfolder: str, max_size: tuple = (400, 400)) -> str:
    """
    Resize and save an uploaded image.
    Returns the filename (not the full path).
    """
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    random_hex = secrets.token_hex(12)
    filename = f"{random_hex}.{ext}"

    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    full_path = os.path.join(upload_path, filename)

    img = Image.open(file_storage)
    img.thumbnail(max_size, Image.LANCZOS)

    # Convert RGBA → RGB so JPEG saves cleanly
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(full_path, optimize=True, quality=85)
    return filename


def delete_file(subfolder: str, filename: str) -> None:
    """Remove an old upload file if it isn't the default placeholder."""
    if not filename or filename == "default.png":
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder, filename)
    if os.path.exists(path):
        os.remove(path)


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def paginate_query(query, page: int, per_page: int = 20):
    return query.paginate(page=page, per_page=per_page, error_out=False)
