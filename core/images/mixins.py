from django.db import models

from core.images.processors import process_image
from core.images.services import get_or_create_image_version
from core.images.state import image_changed
from core.images.storage import cleanup_image_files


class ImageOptimizationsMixin:
    """
    Reusable image handling mixin.
    """

    image_field_name = "image"

    class Meta:
        abstract = False

    def save(self, *args, **kwargs):
        image_field = getattr(
            self,
            self.image_field_name,
            None,
        )

        old_image_name = None

        if self.pk and image_changed(
            self,
            self.image_field_name,
        ):
            old_instance = type(self).objects.filter(pk=self.pk).first()

            if old_instance:
                old_image = getattr(
                    old_instance,
                    self.image_field_name,
                )

                if old_image:
                    old_image_name = old_image.name

        super().save(*args, **kwargs)

        image_field = getattr(
            self,
            self.image_field_name,
            None,
        )

        if image_field:
            if image_field:
                try:
                    process_image(
                        source_path=image_field.path,
                    )
                except Exception as e:
                    print(e)

        if old_image_name:
            cleanup_image_files(
                self,
                old_image_name,
            )
