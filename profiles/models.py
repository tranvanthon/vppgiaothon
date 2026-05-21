from django.db import models
import os, glob
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from core.paths.upload import original_upload_path
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Bạn phải cung cấp email.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "customer")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser phải có is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser phải có is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("admin", "Quản trị viên"),
        ("staff", "Nhân viên"),
        ("customer", "Khách hàng"),
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customer")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Danh sách người dùng"

    def get_role_code(self):
        return self.role

    def get_full_name(self):
        return self.name or self.email

    def get_short_name(self):
        return self.name or self.email.split("@")[0]

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff_role(self):
        return self.role == "staff"


class Profile(models.Model):
    SEX_CHOICES = [
        ("M", "Nam"),
        ("F", "Nữ"),
        ("O", "Khác"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(upload_to=original_upload_path, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default="M")
    bio = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # 1. Kiểm tra nếu user THAY ĐỔI hoặc XÓA avatar
        if self.pk:
            old_instance = type(self).objects.filter(pk=self.pk).first()
            if (
                old_instance
                and old_instance.avatar
                and old_instance.avatar != self.avatar
            ):
                old_avatar_name = old_instance.avatar.name

                # A. Xóa file ảnh gốc
                try:
                    if default_storage.exists(old_avatar_name):
                        default_storage.delete(old_avatar_name)
                except Exception as e:
                    print(f"Lỗi khi xóa ảnh gốc: {e}")

                # B. Quét và xóa TẤT CẢ các bản sao lưu, bản resize liên quan đến file cũ
                try:
                    filename = os.path.basename(old_avatar_name)
                    app_name = self._meta.app_label
                    model_name = self._meta.model_name
                    base_dir_relative = os.path.join("uploads", app_name, model_name)
                    base_dir_absolute = default_storage.path(base_dir_relative)

                    search_pattern = os.path.join(base_dir_absolute, "**", filename)
                    found_files = glob.glob(search_pattern, recursive=True)

                    for file_path in found_files:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            print(f"Lỗi khi xóa file: {file_path} - {e}")

                except Exception as e:
                    print(f"Lỗi khi quét dọn ảnh cache resize: {e}")

        # 2. Thực hiện lưu model
        super().save(*args, **kwargs)

        # 3. Tối ưu ảnh gốc (resize nếu quá lớn)
        if self.avatar and default_storage.exists(self.avatar.name):
            try:
                img = Image.open(self.avatar.path)
                if img.width > 1200 or img.height > 1200:
                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                img.save(self.avatar.path, optimize=True, quality=85)
            except Exception as e:
                print(f"Lỗi xử lý tối ưu ảnh gốc: {e}")

    @property
    def display_avatar(self):
        """Trả về URL avatar hoặc avatar mặc định"""
        if self.avatar and default_storage.exists(self.avatar.name):
            return self.avatar.url
        else:
            return "/static/images/default/avatar.png"

    def __str__(self):
        return self.user.email
