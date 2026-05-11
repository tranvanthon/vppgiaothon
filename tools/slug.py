from slugify import slugify


def generate_unique_slug(instance, value, slug_field_name="slug"):
    slug = slugify(value)
    ModelClass = instance.__class__

    if not slug:
        slug = "item"

    unique_slug = slug
    counter = 1

    while True:
        # Kiểm tra slug đã tồn tại chưa
        exists = ModelClass.objects.filter(**{slug_field_name: unique_slug})

        if instance.pk:
            exists = exists.exclude(pk=instance.pk)

        if not exists.exists():
            break

        unique_slug = f"{slug}-{counter}"
        counter += 1

    return unique_slug
