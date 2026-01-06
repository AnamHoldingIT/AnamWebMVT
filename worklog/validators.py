# worklog/validators.py
from django.core.exceptions import PermissionDenied
from django.utils import timezone


def _aware(dt):
    if not dt:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def assert_plan_editable(plan):
    locked_at = _aware(plan.locked_at)
    if locked_at and timezone.now() >= locked_at:
        raise PermissionDenied("برنامه این روز قفل شده و قابل ویرایش نیست.")


def assert_report_editable(report):
    now = timezone.now()
    locked_at = _aware(report.locked_at)

    if now.date() != report.date:
        raise PermissionDenied("گزارش فقط در همان روز قابل تکمیل است.")
    if locked_at and now >= locked_at:
        raise PermissionDenied("مهلت ویرایش گزارش به پایان رسیده است.")


def validate_time_range(start, end):
    if start >= end:
        raise ValueError("ساعت شروع باید قبل از ساعت پایان باشد.")
