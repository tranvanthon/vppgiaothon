from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image
from io import BytesIO
from .models import Profile

User = get_user_model()
import requests


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Nếu email đã tồn tại ==> link account thay vì tạo mới
        """
        if sociallogin.is_existing:
            return
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        """
        Map dữ liệu từ Google → CustomUser
        """
        user = super().populate_user(request, sociallogin, data)
        user.email = data.get("email")
        user.name = data.get("name", "")

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # ✅ đảm bảo profile tồn tại
        profile = getattr(user, "profile", None)

        if not profile:
            profile = Profile.objects.create(user=user)

        picture_url = sociallogin.account.extra_data.get("picture")

        if picture_url:
            self.save_avatar(user, picture_url)

        return user

    def save_avatar(self, user, url):
        try:

            response = requests.get(url)
            if response.status_code != 200:
                return

            image = Image.open(BytesIO(response.content))

            if image.mode == "RGBA":
                image = image.convert("RGB")

            buffer = BytesIO()
            image.save(buffer, format="JPEG")

            filename = slugify(user.email) + ".jpg"

            profile = user.profile  # chắc chắn đã tồn tại

            profile.avatar.save(filename, ContentFile(buffer.getvalue()), save=True)

        except Exception as e:
            print("Error saving avatar:", e)
