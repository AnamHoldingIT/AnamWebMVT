# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "username",
        "full_name",
        "email",
        "phone",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )

    search_fields = (
        "username",
        "full_name",
        "email",
        "phone",
    )

    ordering = ("-date_joined",)

    fieldsets = (
        ("اطلاعات ورود", {
            "fields": ("username", "password")
        }),

        ("اطلاعات شخصی", {
            "fields": ("full_name", "email", "phone")
        }),

        ("نقش و دسترسی‌ها", {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),

        ("زمان‌ها", {
            "fields": ("date_joined",)
        }),
    )

    add_fieldsets = (
        ("ایجاد کاربر جدید", {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "role", "is_staff", "is_superuser"),
        }),
    )

    readonly_fields = ("date_joined",)
