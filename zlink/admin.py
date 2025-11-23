# zlink/admin.py

from django.contrib import admin

from .models import ReCode


@admin.register(ReCode)
class ReCodeAdmin(admin.ModelAdmin):
    # چی‌ها تو لیست اصلی نشون داده بشه
    list_display = (
        "full_name",
        "phone",
        "status",
        "created_at",
        "updated_at",
    )

    # روی اینا کلیک می‌کنی می‌ره صفحه جزئیات
    list_display_links = ("full_name", "phone")

    # فیلترهای سایدبار
    list_filter = (
        "status",
        "created_at",
    )

    # سرچ
    search_fields = (
        "first_name",
        "last_name",
        "phone",
    )
    search_help_text = "جستجو بر اساس نام، نام خانوادگی یا شماره تماس"

    # ترتیب پیش‌فرض
    ordering = ("-created_at",)

    # فیلدهای فقط‌خواندنی
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    # چیدمان فرم داخل پنل ادمین
    fieldsets = (
        (
            "اطلاعات متقاضی",
            {
                "fields": (
                    ("first_name", "last_name"),
                    "phone",
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
                "classes": ("collapse",),  # این بخش جمع‌شونده باشه
            },
        ),
    )

    # اکشن‌ها (بالای لیست)
    actions = ("reset_status_to_new",)

    @admin.action(description="بازگردانی وضعیت به «جدید» برای موارد انتخاب‌شده")
    def reset_status_to_new(self, request, queryset):
        """
        همه موارد انتخاب‌شده رو برمی‌گردونه به وضعیت اولیه (STATUS_NEW)
        """
        from home.models import STATUS_NEW  # این‌جا ایمپورتش می‌کنیم که حلقه‌ای نشه

        updated = queryset.update(status=STATUS_NEW)
        self.message_user(
            request,
            f"وضعیت {updated} درخواست با موفقیت به «جدید» تغییر کرد.",
        )
