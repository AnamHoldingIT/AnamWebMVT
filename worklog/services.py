# worklog/services.py
from datetime import datetime, time, timedelta
from django.db import transaction
from django.utils import timezone

from .models import (
    DailyPlan,
    DailyReport,
    DailyScheduleBlock,
    ReportEntry,
    ReportStatus,
)


# ---------- helpers ----------

def calc_plan_locked_at(date):
    # 12 شب روز قبل
    prev_day = date - timedelta(days=1)
    return timezone.make_aware(datetime.combine(prev_day, time(23, 59, 59)))


def calc_report_locked_at(date):
    # 12 شب همان روز
    return timezone.make_aware(datetime.combine(date, time(23, 59, 59)))


# ---------- plan ----------

@transaction.atomic
def get_or_create_plan(member, date):
    plan, created = DailyPlan.objects.get_or_create(
        project_member=member,
        date=date,
        defaults={
            "locked_at": calc_plan_locked_at(date),
        }
    )
    return plan


def ensure_plan_editable(plan):
    from .validators import assert_plan_editable
    assert_plan_editable(plan)


# ---------- report ----------

@transaction.atomic
# worklog/services.py

@transaction.atomic
def get_or_create_today_report(member, plan):
    today = timezone.localdate()
    report, created = DailyReport.objects.get_or_create(
        project_member=member,
        date=today,
        defaults={
            "plan": plan,
            "locked_at": calc_report_locked_at(today),
        }
    )
    return report, created



@transaction.atomic
def sync_report_entries_from_plan(report):
    """
    Lazy sync:
    فقط entry هایی که وجود ندارن ساخته می‌شن
    """
    plan_blocks = (
        DailyScheduleBlock.objects
        .filter(plan=report.plan)
        .only("id")
    )

    existing_block_ids = set(
        ReportEntry.objects
        .filter(report=report)
        .values_list("schedule_block_id", flat=True)
    )

    new_entries = []
    for block in plan_blocks:
        if block.id not in existing_block_ids:
            new_entries.append(
                ReportEntry(
                    report=report,
                    schedule_block=block,
                    status=ReportStatus.NOT_DONE,
                )
            )

    if new_entries:
        ReportEntry.objects.bulk_create(new_entries)


def ensure_report_editable(report):
    from .validators import assert_report_editable
    assert_report_editable(report)


