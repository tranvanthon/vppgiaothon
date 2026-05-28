

def image_changed(instance, field_name):
    """
    Return True if file field changed.
    """
    if not instance.pk:
        return True

    old = type(instance).objects.filter(pk=instance.pk).first()
    if not old:
        return True

    old_file = getattr(old, field_name)
    new_file = getattr(instance, field_name)

    return old_file != new_file