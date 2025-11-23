# home/admin.py

from django.contrib import admin
from .models import Contract, SiteStat


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "startup_name",
        "status",
        "is_read",
        "created_at",
    )
    list_filter = (
        "status",
        "is_read",
        "created_at",
    )
    search_fields = (
        "full_name",
        "phone",
        "startup_name",
        "email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("اطلاعات متقاضی", {
            "fields": (
                "full_name",
                "phone",
                "email",
            )
        }),
        ("اطلاعات استارتاپ / ایده", {
            "fields": (
                "startup_name",
                "detail",
            )
        }),
        ("وضعیت و متادیتا", {
            "fields": (
                "status",
                "is_read",
                "created_at",
                "updated_at",
            )
        }),
    )

    # اکشن‌های سریع برای ادمین (دلخواه ولی باحال)
    @admin.action(description="علامت‌گذاری به‌عنوان خوانده شده")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="علامت‌گذاری به‌عنوان خوانده نشده")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    actions = ["mark_as_read", "mark_as_unread"]


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ("total_views", "updated_at")
    readonly_fields = ("total_views", "updated_at")

    def has_add_permission(self, request):
        """
        فقط همون رکورد solo رو داشته باشیم،
        نذار ادمین چندتا رکورد SiteStat بسازه.
        """
        if SiteStat.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # نذار پاکش کنن، چون آمار سایت هست
        return False
