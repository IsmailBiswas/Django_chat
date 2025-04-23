from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa
from .base import env

if "DJANGO_SECRET_KEY" not in env:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is not set")

SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "django", "192.168.1.5"]
ROOT_URLCONF = "dchat.urls"

EMAIL_HOST = env("EMAIL_HOST", default="mailpit")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")

POSTGRES_HOST = env("POSTGRES_HOST")
POSTGRES_PORT = env("POSTGRES_PORT")
POSTGRES_DB = env("POSTGRES_DB")
POSTGRES_USER = env("POSTGRES_USER")
POSTGRES_PASSWORD = env("POSTGRES_PASSWORD")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    }
}

ASGI_APPLICATION = "dchat.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}

MEDIA_ROOT = "/storage/prod"
DCHAT_MEDIA_URL = "http://192.168.1.5/storage/prod"
DCHAT_FILE_ACCESS_VALIDITY = 3600
