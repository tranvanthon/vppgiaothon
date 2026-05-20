import os

from django.db import transaction
from django.core.files.storage import (
    default_storage,
)

from core.paths.upload import (
    thumb_upload_path,
    medium_upload_path,
)

from core.utils.image import (
    create_versions,
)


class ImageMixin:

    image_field = "image"

    thumb_field = "thumbnail"

    medium_field = "medium"

    thumb_size = (
        300,
        300,
    )

    medium_size = (
        800,
        800,
    )

    resize_mode = "crop"

    def collect_files(self):

        files = []

        for field_name in [
            self.image_field,
            self.thumb_field,
            self.medium_field,
        ]:

            field = getattr(
                self,
                field_name,
                None,
            )

            if field and field.name:
                files.append(field.name)

        return files

    def delete_files(
        self,
        paths,
    ):

        for path in paths:

            try:

                if path and default_storage.exists(path):

                    default_storage.delete(path)

            except Exception:
                pass

    def generate_images(
        self,
    ):

        image = getattr(
            self,
            self.image_field,
            None,
        )

        if not image or not image.name:
            return

        filename = os.path.basename(image.name)

        thumb_relative = thumb_upload_path(
            self,
            filename,
        )

        medium_relative = medium_upload_path(
            self,
            filename,
        )

        thumb_absolute = default_storage.path(thumb_relative)

        medium_absolute = default_storage.path(medium_relative)

        os.makedirs(
            os.path.dirname(thumb_absolute),
            exist_ok=True,
        )

        os.makedirs(
            os.path.dirname(medium_absolute),
            exist_ok=True,
        )

        create_versions(
            image.path,
            thumb_absolute,
            medium_absolute,
            self.thumb_size,
            self.medium_size,
            mode=self.resize_mode,
        )

        getattr(
            self,
            self.thumb_field,
        ).name = thumb_relative

        getattr(
            self,
            self.medium_field,
        ).name = medium_relative

    def save(
        self,
        *args,
        **kwargs,
    ):

        is_new = self.pk is None

        old_files = []

        image_changed = False

        if not is_new:

            old_instance = type(self).objects.filter(pk=self.pk).first()

            if old_instance:

                old_image = getattr(
                    old_instance,
                    self.image_field,
                )

                new_image = getattr(
                    self,
                    self.image_field,
                )

                if old_image and old_image != new_image:

                    image_changed = True

                    old_files = old_instance.collect_files()

        super().save(
            *args,
            **kwargs,
        )

        if is_new or image_changed:

            self.generate_images()

            type(self).objects.filter(pk=self.pk).update(
                **{
                    self.thumb_field: getattr(
                        self,
                        self.thumb_field,
                    ).name,
                    self.medium_field: getattr(
                        self,
                        self.medium_field,
                    ).name,
                }
            )

            if old_files:

                transaction.on_commit(lambda: self.delete_files(old_files))

    def hard_delete(
        self,
        *args,
        **kwargs,
    ):

        files = self.collect_files()

        super().delete(
            *args,
            **kwargs,
        )

        transaction.on_commit(lambda: self.delete_files(files))
