import os
import glob
from django.core.files.storage import default_storage


def delete_image_versions(instance, image_name):
    """
    Xóa ảnh gốc + toàn bộ bản resize/cache liên quan.

    Ví dụ:
    uploads/accounts/profile/original/2026/05/avatar123.jpg

    sẽ xóa:
    uploads/accounts/profile/original/2026/05/avatar123.jpg
    uploads/accounts/profile/resized_50x50_crop/2026/05/avatar123.webp
    uploads/accounts/profile/resized_100x100_crop/2026/05/avatar123.webp
    ...
    """

    if not image_name:
        return

    try:
        # xóa file gốc
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

        search_pattern = os.path.join(base_absolute, "**", f"{stem}.*")

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
