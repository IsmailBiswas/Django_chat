from django.contrib import admin

from .models import Connection, Group, Message

admin.site.register(Connection)
admin.site.register(Group)
admin.site.register(Message)
