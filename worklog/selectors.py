# worklog/selectors.py
from datetime import date as date_cls
from django.db.models import Prefetch

from .models import (
    Project,
    ProjectMember,
    DailyPlan,
    DailyReport,
    DailyScheduleBlock,
    ReportEntry,
)


def get_active_membership(user, project_id):
    return (
        ProjectMember.objects
        .select_related("project")
        .filter(
            user=user,
            project_id=project_id,
            is_active=True,
            project__is_active=True
        )
        .first()
    )


def list_user_active_projects(user):
    return (
        Project.objects
        .filter(
            members__user=user,
            members__is_active=True,
            is_active=True
        )
        .distinct()
        .order_by("title")
    )


def get_plan(member, date):
    return (
        DailyPlan.objects
        .filter(project_member=member, date=date)
        .first()
    )


def get_plan_with_details(member, date):
    return (
        DailyPlan.objects
        .select_related("project_member", "project_member__project")
        .prefetch_related(
            "achievements",
            "schedule_blocks",
        )
        .filter(project_member=member, date=date)
        .first()
    )


def get_report(member, date):
    return (
        DailyReport.objects
        .filter(project_member=member, date=date)
        .first()
    )


def get_report_with_entries(member, date):
    return (
        DailyReport.objects
        .select_related("project_member", "plan")
        .prefetch_related(
            Prefetch(
                "entries",
                queryset=ReportEntry.objects.select_related("schedule_block"),
            ),
            "extra_actions",
        )
        .filter(project_member=member, date=date)
        .first()
    )
