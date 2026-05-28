import os
from PIL import Image
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
}
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024


# Kiểm tra phần mở rộng của file ảnh
def validate_image_extension(file):
    _, ext = os.path.splitext(file.name)

    ext = ext.lower().lstrip(".")

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Unsupported image format.")


# Kiểm tra kích thước file ảnh
def validate_image_size(file):
    if file.size > MAX_IMAGE_UPLOAD_SIZE:
        raise ValidationError("Image file too large.")


# Kiểm tra xem file có phải là ảnh hợp lệ hay không
def validate_image_content(file):
    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError("Invalid image file.")
