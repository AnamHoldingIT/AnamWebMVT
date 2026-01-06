# worklog/models.py
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Project(models.Model):
    title = models.CharField(max_length=200)
    sheet_url = models.URLField("Google Sheet Link")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectMember(models.Model):
    ROLE_MEMBER = "member"
    ROLE_MANAGER = "manager"

    ROLE_CHOICES = (
        (ROLE_MEMBER, "عضو"),
        (ROLE_MANAGER, "مدیر پروژه"),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER
    )

    can_edit_plan = models.BooleanField(default=True)
    can_submit_report = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("project", "user")
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["project", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.project}"


class DailyPlan(models.Model):
    project_member = models.ForeignKey(
        ProjectMember,
        on_delete=models.PROTECT,
        related_name="daily_plans"
    )

    date = models.DateField()
    locked_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project_member", "date")
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["project_member", "date"]),
        ]

    def __str__(self):
        return f"Plan {self.date} - {self.project_member}"


class DailyAchievement(models.Model):
    plan = models.ForeignKey(
        DailyPlan,
        on_delete=models.CASCADE,
        related_name="achievements"
    )
    title = models.CharField(max_length=255)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class DailyScheduleBlock(models.Model):
    plan = models.ForeignKey(
        DailyPlan,
        on_delete=models.CASCADE,
        related_name="schedule_blocks"
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    task_title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_required = models.BooleanField(default=False)

    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["plan", "start_time"]),
        ]

    def __str__(self):
        return f"{self.start_time}-{self.end_time} | {self.task_title}"


class DailyReport(models.Model):
    project_member = models.ForeignKey(
        ProjectMember,
        on_delete=models.PROTECT,
        related_name="daily_reports"
    )

    plan = models.ForeignKey(
        DailyPlan,
        on_delete=models.PROTECT,
        related_name="reports"
    )

    date = models.DateField()
    locked_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project_member", "date")
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["project_member", "date"]),
        ]

    def __str__(self):
        return f"Report {self.date} - {self.project_member}"


class ReportStatus(models.IntegerChoices):
    NOT_DONE = 0, "انجام نشده"
    IN_PROGRESS = 1, "در دست انجام"
    DONE = 2, "انجام شده"
    BLOCKED = 3, "مسدود شده"
    PARTIAL = 4, "ناقص"


class ReportEntry(models.Model):
    report = models.ForeignKey(
        DailyReport,
        on_delete=models.CASCADE,
        related_name="entries"
    )
    schedule_block = models.ForeignKey(
        DailyScheduleBlock,
        on_delete=models.CASCADE,
        related_name="report_entries"
    )

    status = models.PositiveSmallIntegerField(
        choices=ReportStatus.choices
    )
    note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("report", "schedule_block")
        indexes = [
            models.Index(fields=["schedule_block"]),
        ]

    def __str__(self):
        return f"{self.schedule_block} → {self.get_status_display()}"


class ReportExtraAction(models.Model):
    report = models.ForeignKey(
        DailyReport,
        on_delete=models.CASCADE,
        related_name="extra_actions"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ReportAchievement(models.Model):
    report = models.ForeignKey(
        DailyReport,
        on_delete=models.CASCADE,
        related_name="achievement_states"
    )
    achievement = models.ForeignKey(
        DailyAchievement,
        on_delete=models.CASCADE,
        related_name="report_states"
    )
    achieved = models.BooleanField(default=False)

    class Meta:
        unique_together = ("report", "achievement")
        indexes = [
            models.Index(fields=["report"]),
            models.Index(fields=["achievement"]),
        ]

    def __str__(self):
        return f"{self.achievement} => {self.achieved}"
