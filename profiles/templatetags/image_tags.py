from django import template
from core.images.services import get_or_create_image_version
from django.core.files.storage import default_storage

register = template.Library()


@register.filter(name="get_avatar_url")
def get_avatar_url(user, size_str):
    """
    Sử dụng trong template: {{ user|get_avatar_url:"50,50" }}
    """
    DEFAULT_AVATAR = "/static/images/default/avatar.png"
    if not user or user.is_anonymous:
        return DEFAULT_AVATAR
    # Lấy profile từ user
    try:
        profile = user.profile

        if not profile.avatar or not default_storage.exists(profile.avatar.name):
            return DEFAULT_AVATAR

        width, height = map(int, size_str.split(","))

        # Gọi hàm dịch vụ sinh ảnh resize
        avatar_url = get_or_create_image_version(
            profile, "avatar", width, height, mode="crop"
        )
        return avatar_url or DEFAULT_AVATAR
    except Exception as e:
        print(e)
        return DEFAULT_AVATAR
