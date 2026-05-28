import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Profile


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class UploadAvatarTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="avatar@example.com",
            password="password123",
        )
        self.client.force_login(self.user)

    def make_image_file(self, name="avatar.png"):
        buffer = BytesIO()
        Image.new("RGB", (64, 64), color=(20, 120, 200)).save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    def test_upload_avatar_updates_profile(self):
        response = self.client.post(
            reverse("upload_avatar"),
            {"avatar": self.make_image_file()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar)
        self.assertIn("/media/uploads/profiles/profile/original/", response.json()["avatar_url"])

    def test_upload_avatar_rejects_invalid_image(self):
        response = self.client.post(
            reverse("upload_avatar"),
            {
                "avatar": SimpleUploadedFile(
                    "avatar.png",
                    b"not an image",
                    content_type="image/png",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
