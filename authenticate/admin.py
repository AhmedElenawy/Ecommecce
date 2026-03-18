# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin

# Unregister the default User admin
admin.site.unregister(User)

# Re-register with Unfold
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass