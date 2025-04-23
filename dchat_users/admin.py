from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DchatUser, Verification

admin.site.register(DchatUser, UserAdmin)
admin.site.register(Verification)
