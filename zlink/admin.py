# zlink/admin.py

from django.contrib import admin
from .models import ReCode, Referrer


@admin.register(ReCode)
class ReCodeAdmin(admin.ModelAdmin):
    # =========================
    # لیست اصلی
    # =========================
    list_display = (
        "full_name",
        "phone",
        "email",
        "city",
        "referrer",  # ✅ معرف
        "status",
        "created_at",
        "updated_at",
    )

    list_display_links = ("full_name", "phone")

    # =========================
    # فیلترهای سایدبار
    # =========================
    list_filter = (
        "status",
        "city",
        "referrer",  # ✅ فیلتر بر اساس معرف
        "created_at",
    )

    # =========================
    # جستجو
    # =========================
    search_fields = (
        "first_name",
        "last_name",
        "phone",
        "email",
        "city",
        "referrer__name",  # ✅ جستجو روی نام معرف
        "referrer__code",  # ✅ جستجو روی کد معرف
    )

    search_help_text = (
        "جستجو بر اساس نام، شماره، ایمیل، شهر یا معرف"
    )

    # =========================
    # ترتیب
    # =========================
    ordering = ("-created_at",)

    # =========================
    # فیلدهای فقط‌خواندنی
    # =========================
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # =========================
    # فرم جزئیات
    # =========================
    fieldsets = (
        (
            "اطلاعات متقاضی",
            {
                "fields": (
                    ("first_name", "last_name"),
                    "phone",
                    "email",
                    "city",
                    "referrer",  # ✅ نمایش معرف
                )
            },
        ),
        (
            "وضعیت و یادداشت داخلی",
            {
                "fields": (
                    "status",
                    "notes",
                )
            },
        ),
        (
            "متادیتا",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    # =========================
    # اکشن‌ها
    # =========================
    actions = ("reset_status_to_new",)

    @admin.action(description="بازگردانی وضعیت به «جدید» برای موارد انتخاب‌شده")
    def reset_status_to_new(self, request, queryset):
        from home.models import STATUS_NEW
        updated = queryset.update(status=STATUS_NEW)
        self.message_user(
            request,
            f"وضعیت {updated} درخواست با موفقیت به «جدید» تغییر کرد.",
        )


# ==================================================
# ادمین معرف‌ها (خیلی مهم برای مدیریت لینک‌ها)
# ==================================================

@admin.register(Referrer)
class ReferrerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "is_active",
        "created_at",
        "recode_count",
    )

    list_filter = ("is_active", "created_at")
    search_fields = ("name", "code")
    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "اطلاعات معرف",
            {
                "fields": (
                    "name",
                    "code",
                    "is_active",
                )
            },
        ),
        (
            "متادیتا",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def recode_count(self, obj):
        return obj.recode_requests.count()

    recode_count.short_description = "تعداد ثبت‌نام"
