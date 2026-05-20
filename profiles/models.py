from django.db import models
import os
from tools.get_upload_path import get_upload_path
from django.conf import settings
from PIL import Image
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
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
    avatar = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default="M")
    bio = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.avatar == self.avatar:
                return super().save(*args, **kwargs)

        super().save(*args, **kwargs)

        if self.avatar:
            try:
                img = Image.open(self.avatar.path)

                if img.width > 300 or img.height > 300:
                    img.thumbnail((300, 300))

                img.save(self.avatar.path, optimize=True, quality=70)

            except FileNotFoundError:
                print("Image file not found, skip processing")

    @property
    def display_avatar(self):
        """Trả về URL avatar hoặc avatar mặc định"""
        if self.avatar and os.path.exists(self.avatar.path):
            return self.avatar.url
        else:
            return "/static/images/default/avatar.png"

    def __str__(self):
        return self.user.email
