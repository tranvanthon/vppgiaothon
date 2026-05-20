import os
import uuid

from datetime import datetime


def build_upload_path(
    instance,
    filename,
    image_type="original",
):

    now = datetime.now()

    year = now.strftime("%Y")

    month = now.strftime("%m")

    app_name = instance._meta.app_label

    model_name = instance._meta.model_name

    ext = filename.split(".")[-1].lower()

    unique_name = f"{uuid.uuid4()}.{ext}"

    return os.path.join(
        "uploads",
        app_name,
        model_name,
        image_type,
        year,
        month,
        unique_name,
    )


def original_upload_path(
    instance,
    filename,
):
    return build_upload_path(
        instance,
        filename,
        "original",
    )


def thumb_upload_path(
    instance,
    filename,
):
    return build_upload_path(
        instance,
        filename,
        "thumb",
    )


def medium_upload_path(
    instance,
    filename,
):
    return build_upload_path(
        instance,
        filename,
        "medium",
    )
