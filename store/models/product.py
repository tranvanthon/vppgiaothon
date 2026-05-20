from django.db import models

from core.mixins.image_mixins import ImageMixin

from core.paths.upload import (
    original_upload_path,
    thumb_upload_path,
    medium_upload_path,
)


class Product(ImageMixin, models.Model):

    name = models.CharField(max_length=200)

    image = models.ImageField(upload_to=original_upload_path)

    thumbnail = models.ImageField(upload_to=thumb_upload_path, blank=True, null=True)

    medium = models.ImageField(upload_to=medium_upload_path, blank=True, null=True)
