from django.contrib import admin
from django.utils.html import format_html

from .models import (
    PortfolioProject,
    ProjectCategory,
    ProjectRole,
    ProjectRoleAssignment,
    ProjectHighlight,
    ProjectMetric,
    ProjectJourneyStep,
)


# ==========================
#  INLINE های حرفه‌ای
# ==========================

class RoleAssignmentInline(admin.TabularInline):
    model = ProjectRoleAssignment
    extra = 1
    autocomplete_fields = ["role"]
    ordering = ["order"]
    fields = ("role", "order")
    show_change_link = True


class HighlightInline(admin.TabularInline):
    model = ProjectHighlight
    extra = 1
    ordering = ["order"]
    fields = ("text", "icon_class", "order")


class MetricInline(admin.TabularInline):
    model = ProjectMetric
    extra = 1
    ordering = ["order"]
    fields = ("label", "value", "order")


class JourneyStepInline(admin.TabularInline):
    model = ProjectJourneyStep
    extra = 1
    ordering = ["step_number"]
    fields = ("step_number", "title", "description")


# ==========================
#  CATEGORY ADMIN
# ==========================

@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon_preview")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]
    fields = ("name", "slug", "icon_class")  # فیلد آیکن در فرم

    @admin.display(description="آیکن")
    def icon_preview(self, obj):
        if getattr(obj, "icon_class", None):
            return format_html("<i class='bi {}'></i>", obj.icon_class)
        return "-"


# ==========================
#  PROJECT ROLE ADMIN
# ==========================

@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["title"]


# ==========================
#  PROJECT ADMIN اصلی
# ==========================

@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):

    list_display = (
        "name_fa",
        "category",
        "status",
        "is_featured_home",
        "list_order",
        "home_order",
        "created_at",
        "thumbnail",
    )

    list_filter = ("status", "category", "is_featured_home", "created_at")

    search_fields = ("name_fa", "name_en", "short_tagline", "slug")

    prepopulated_fields = {"slug": ("name_en",)}

    fieldsets = (
        ("مشخصات عمومی", {
            "fields": (
                "name_fa",
                "name_en",
                "slug",
                "category",
                "status",
                "collaboration_model",
                "short_tagline",   # 👈 فقط همین‌جا
            )
        }),

        ("متن‌های نمایشی (جزئیات)", {
            "fields": (
                "hero_subtitle",
                "list_summary",
                "detail_summary",
            ),
            "classes": ("collapse",),
        }),

        ("تصاویر", {"fields": ("image",)}),

        ("نمایش در سایت", {
            "fields": (
                "is_featured_home",
                "home_order",
                "list_order",
            ),
            "classes": ("collapse",),
        }),

        ("زمان‌ها", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")

    inlines = [
        RoleAssignmentInline,
        HighlightInline,
        MetricInline,
        JourneyStepInline,
    ]

    autocomplete_fields = ["category"]

    ordering = ["list_order", "home_order", "-created_at"]

    @admin.display(description="تصویر")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                "<img src='{}' width='55' height='55' style='border-radius:8px; object-fit:cover;'/>",
                obj.image.url,
            )
        return "-"

# ==========================
#  سایر مدل‌ها
# ==========================

@admin.register(ProjectRoleAssignment)
class ProjectRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("project", "role", "order")
    autocomplete_fields = ["project", "role"]
    ordering = ["project", "order"]


@admin.register(ProjectHighlight)
class ProjectHighlightAdmin(admin.ModelAdmin):
    list_display = ("project", "text", "order")
    autocomplete_fields = ["project"]
    ordering = ["project", "order"]


@admin.register(ProjectMetric)
class ProjectMetricAdmin(admin.ModelAdmin):
    list_display = ("project", "label", "value", "order")
    autocomplete_fields = ["project"]
    ordering = ["project", "order"]


@admin.register(ProjectJourneyStep)
class ProjectJourneyStepAdmin(admin.ModelAdmin):
    list_display = ("project", "step_number", "title")
    autocomplete_fields = ["project"]
    ordering = ["project", "step_number"]
