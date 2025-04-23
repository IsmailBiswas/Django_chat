from .base import *  # noqa
from .base import env

DEBUG = True

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="PVATtcutfiqaLfQdAr5k9AvgSQrlqF6Y9ugZHSc9fIkbPvWm3FyWe2u4xtQjctiY",
)

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]
ROOT_URLCONF = "dchat.urls"


EMAIL_HOST = env("EMAIL_HOST", default="mailpit")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = env("EMAIL_PORT", default="1025")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")

POSTGRES_HOST = env("POSTGRES_HOST")
POSTGRES_PORT = env("POSTGRES_PORT")
POSTGRES_DB = env("POSTGRES_DB")
POSTGRES_USER = env("POSTGRES_USER")
POSTGRES_PASSWORD = env("POSTGRES_PASSWORD")
