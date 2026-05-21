import os
import glob
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.core.files.storage import default_storage
from profiles.models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()


@receiver(post_delete, sender=Profile)
def delete_profile_image_files(sender, instance, **kwargs):
    """Xóa tất cả file ảnh liên quan khi xóa Profile"""
    
    if not instance.avatar or not instance.avatar.name:
        return
    
    old_avatar_name = instance.avatar.name
    filename = os.path.basename(old_avatar_name)
    
    # Xóa file ảnh gốc
    try:
        if default_storage.exists(old_avatar_name):
            default_storage.delete(old_avatar_name)
    except Exception as e:
        print(f"Lỗi khi xóa ảnh gốc: {e}")
    
    # Quét và xóa tất cả bản resize liên quan
    try:
        app_name = sender._meta.app_label
        model_name = sender._meta.model_name
        base_dir_relative = os.path.join("uploads", app_name, model_name)
        base_dir_absolute = default_storage.path(base_dir_relative)
        
        if os.path.exists(base_dir_absolute):
            search_pattern = os.path.join(base_dir_absolute, "**", filename)
            found_files = glob.glob(search_pattern, recursive=True)
            
            for file_path in found_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Lỗi khi xóa file: {file_path} - {e}")
    
    except Exception as e:
        print(f"Lỗi khi quét dọn ảnh cache: {e}")
