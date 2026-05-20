from pathlib import Path
import os
from django.contrib.messages import constants as messages

# Custom messages
MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-yvj#qs&$b3me43$gwm%1b+$w3^ch16idgilyk&2$v43ij-6njg"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["0.0.0.0", "127.0.0.1", "localhost"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Cần cho domain name
    "django.contrib.sites",
    # sripy and boostrap
    "crispy_forms",
    "crispy_bootstrap5",
    # allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # provider Google
    "allauth.socialaccount.providers.google",
    # clean up images uploaded
    "django_cleanup.apps.CleanupConfig",
    "mptt",
    # myapps
    "store",
    "profiles.apps.ProfilesConfig",
]
# custom userform
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Tep tinh cho server gunicorn
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # allauth
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "vppgiaothon.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Cho hiển thị categories mọi nơi trong project
                "vppgiaothon.context_processors.global_categories",
                # Lây ten domail
                "vppgiaothon.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "vppgiaothon.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "vi"

TIME_ZONE = "Asia/Ho_Chi_Minh"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# allauth
# Cấu hình site
AUTH_USER_MODEL = "profiles.CustomUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

# # Cho phep gởi mail khi dev trong terminal
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# # Cho phep gởi mail khi dev bang MailHog

if DEBUG:
    # MailHog sẽ bắt email qua giao thức SMTP[cite: 5]
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "localhost"  # Hoặc 'localhost'
    EMAIL_PORT = 1025  # Cổng mặc định của MailHog
    EMAIL_HOST_USER = ""  # MailHog không cần user
    EMAIL_HOST_PASSWORD = ""  # MailHog không cần password
    EMAIL_USE_TLS = False  # MailHog không cần TLS
    DEFAULT_FROM_EMAIL = "no-reply@vppgiaothon.com"
else:
    # Cấu hình SendGrid khi chạy thực tế (Production)[cite: 5]
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.sendgrid.net"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = "apikey"
    EMAIL_HOST_PASSWORD = os.environ.get("SENDGRID_API_KEY")  # Nên dùng biến môi trường


# ------Cấu hình login, logout

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
SOCIALACCOUNT_LOGIN_ON_GET = True  # Chạy ngay sang trang login with Google luôn
ACCOUNT_LOGOUT_ON_GET = (
    True  # Tự động logout khi nhấn logout không qua template logout.html
)

# # Model không có trường username
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Login with email, pass and signup
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"  # Hoặc "optional"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_ALLOW_REGISTRATION = True

SOCIALACCOUNT_ADAPTER = "profiles.adapters.CustomSocialAccountAdapter"
