import glob
import os

from django.core.files.storage import default_storage


def cleanup_image_files(
    instance,
    image_name,
):
    """
    Delete original image and all related versions.
    """

    if not image_name:
        return

    try:
        if default_storage.exists(image_name):
            default_storage.delete(image_name)

        stem = os.path.splitext(os.path.basename(image_name))[0]

        app_name = instance._meta.app_label
        model_name = instance._meta.model_name

        base_relative = os.path.join(
            "uploads",
            app_name,
            model_name,
        )

        base_absolute = default_storage.path(base_relative)

        if not os.path.exists(base_absolute):
            return

        search_pattern = os.path.join(
            base_absolute,
            "**",
            f"{stem}.*",
        )

        found_files = glob.glob(
            search_pattern,
            recursive=True,
        )

        for file_path in found_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)

            except Exception:
                pass

    except Exception:
        pass
