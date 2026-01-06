# worklog/locks.py
from datetime import datetime, time, timedelta
from django.utils import timezone


def end_of_day(dt):
    return timezone.make_aware(
        datetime.combine(dt, time(23, 59, 59))
    )


def calc_plan_lock(plan_date):
    """
    پلن تا 12 شب روز قبل قابل ویرایش است
    """
    return end_of_day(plan_date - timedelta(days=1))


def calc_report_lock(report_date):
    """
    گزارش تا 12 شب همان روز قابل ویرایش است
    """
    return end_of_day(report_date)


def is_locked(locked_at):
    return timezone.now() >= locked_at
