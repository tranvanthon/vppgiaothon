import os
from django.core.files.storage import default_storage
from core.images.processors import process_image


def get_or_create_image_version(
    instance,
    image_field_name,
    width,
    height,
    mode="crop",
):
    image_field = getattr(
        instance,
        image_field_name,
        None,
    )

    if not image_field or not image_field.name:
        return ""

    original_name = image_field.name

    stem = os.path.splitext(os.path.basename(original_name))[0]

    year, month = os.path.dirname(original_name).split("/")[-2:]

    app_name = instance._meta.app_label
    model_name = instance._meta.model_name

    relative_path = os.path.join(
        "uploads",
        app_name,
        model_name,
        f"resized_{width}x{height}_{mode}",
        year,
        month,
        f"{stem}.webp",
    )

    if default_storage.exists(relative_path):
        return default_storage.url(relative_path)

    absolute_path = default_storage.path(relative_path)

    process_image(
        source_path=image_field.path,
        dest_path=absolute_path,
        size=(width, height),
    )

    return default_storage.url(relative_path)
