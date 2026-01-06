# worklog/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Project,
    ProjectMember,
    DailyPlan,
    DailyAchievement,
    DailyScheduleBlock,
    DailyReport,
    ReportEntry,
    ReportExtraAction,
)


# -------------------------
# Inlines
# -------------------------

class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    autocomplete_fields = ("user",)
    fields = (
        "user",
        "role",
        "can_edit_plan",
        "can_submit_report",
        "is_active",
        "joined_at",
        "left_at",
    )
    readonly_fields = ("joined_at",)


class DailyAchievementInline(admin.TabularInline):
    model = DailyAchievement
    extra = 0
    fields = ("title", "sort_order")
    ordering = ("sort_order", "id")


class DailyScheduleBlockInline(admin.TabularInline):
    model = DailyScheduleBlock
    extra = 0
    fields = (
        "start_time",
        "end_time",
        "task_title",
        "description",
        "is_required",
        "sort_order",
    )
    ordering = ("start_time",)


class ReportEntryInline(admin.TabularInline):
    model = ReportEntry
    extra = 0
    autocomplete_fields = ("schedule_block",)
    fields = ("schedule_block", "status", "note", "updated_at")
    readonly_fields = ("updated_at",)


class ReportExtraActionInline(admin.TabularInline):
    model = ReportExtraAction
    extra = 0
    fields = ("title", "description", "start_time", "end_time", "created_at")
    readonly_fields = ("created_at",)


# -------------------------
# Admins
# -------------------------

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at", "sheet_link")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "sheet_url")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = (ProjectMemberInline,)

    def sheet_link(self, obj):
        if not obj.sheet_url:
            return "-"
        return format_html('<a href="{}" target="_blank">Open Sheet</a>', obj.sheet_url)

    sheet_link.short_description = "Sheet"


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "user",
        "role",
        "is_active",
        "can_edit_plan",
        "can_submit_report",
        "joined_at",
        "left_at",
    )
    list_filter = ("role", "is_active", "can_edit_plan", "can_submit_report", "joined_at")
    search_fields = (
        "project__title",
        "user__username",
        "user__email",
        "user__full_name",
    )
    autocomplete_fields = ("project", "user")
    ordering = ("-joined_at",)
    date_hierarchy = "joined_at"


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ("date", "project_member", "locked_at", "created_at", "updated_at")
    list_filter = ("date",)
    search_fields = (
        "project_member__project__title",
        "project_member__user__username",
        "project_member__user__email",
        "project_member__user__full_name",
    )
    autocomplete_fields = ("project_member",)
    ordering = ("-date", "-created_at")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
    inlines = (DailyAchievementInline, DailyScheduleBlockInline)


@admin.register(DailyAchievement)
class DailyAchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "plan", "sort_order")
    list_filter = ("sort_order",)
    search_fields = (
        "title",
        "plan__project_member__project__title",
        "plan__project_member__user__username",
        "plan__project_member__user__full_name",
    )
    autocomplete_fields = ("plan",)
    ordering = ("sort_order", "id")


@admin.register(DailyScheduleBlock)
class DailyScheduleBlockAdmin(admin.ModelAdmin):
    list_display = ("task_title", "plan", "start_time", "end_time", "is_required", "sort_order")
    list_filter = ("is_required",)
    search_fields = (
        "task_title",
        "plan__project_member__project__title",
        "plan__project_member__user__username",
        "plan__project_member__user__full_name",
    )
    autocomplete_fields = ("plan",)
    ordering = ("plan", "start_time")


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ("date", "project_member", "plan", "locked_at", "created_at", "updated_at")
    list_filter = ("date",)
    search_fields = (
        "project_member__project__title",
        "project_member__user__username",
        "project_member__user__email",
        "project_member__user__full_name",
    )
    autocomplete_fields = ("project_member", "plan")
    ordering = ("-date", "-created_at")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
    inlines = (ReportEntryInline, ReportExtraActionInline)


@admin.register(ReportEntry)
class ReportEntryAdmin(admin.ModelAdmin):
    list_display = ("report", "schedule_block", "status", "updated_at")
    list_filter = ("status", "updated_at")
    search_fields = (
        "report__project_member__project__title",
        "report__project_member__user__username",
        "report__project_member__user__full_name",
        "schedule_block__task_title",
    )
    autocomplete_fields = ("report", "schedule_block")
    ordering = ("-updated_at",)


@admin.register(ReportExtraAction)
class ReportExtraActionAdmin(admin.ModelAdmin):
    list_display = ("title", "report", "start_time", "end_time", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "title",
        "report__project_member__project__title",
        "report__project_member__user__username",
        "report__project_member__user__full_name",
    )
    autocomplete_fields = ("report",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
