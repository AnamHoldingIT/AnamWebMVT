# worklog/forms.py
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    DailyPlan,
    DailyScheduleBlock,
    ReportEntry,
    ReportStatus,
)
from .dates import parse_jalali_date
from .locks import is_locked


# --------------------
# Daily Plan Form
# --------------------
class DailyPlanForm(forms.ModelForm):
    jalali_date = forms.CharField(label="تاریخ (شمسی)", help_text="مثال: 1404-09-26")

    class Meta:
        model = DailyPlan
        fields = []  # چون نمی‌خوای کاربر فیلد date رو مستقیم ببینه

    def clean_jalali_date(self):
        raw = self.cleaned_data["jalali_date"]
        try:
            g_date = parse_jalali_date(raw)
        except ValueError:
            raise ValidationError("فرمت تاریخ شمسی نادرست است")
        return g_date

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk and is_locked(self.instance.locked_at):
            raise ValidationError("این برنامه قفل شده و قابل ویرایش نیست")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.date = self.cleaned_data["jalali_date"]  # اینجا مهمه ✅
        if commit:
            obj.save()
        return obj


# --------------------
# Schedule Block Form
# --------------------
class DailyScheduleBlockForm(forms.ModelForm):
    class Meta:
        model = DailyScheduleBlock
        fields = [
            "start_time",
            "end_time",
            "task_title",
            "description",
            "is_required",
        ]

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and start >= end:
            raise ValidationError("ساعت پایان باید بعد از ساعت شروع باشد")

        return cleaned


# --------------------
# Report Entry Form
# --------------------
class ReportEntryForm(forms.ModelForm):
    class Meta:
        model = ReportEntry
        fields = ["status", "note"]

    def clean(self):
        cleaned = super().clean()
        report = self.instance.report
        if is_locked(report.locked_at):
            raise ValidationError("این گزارش قفل شده و قابل ویرایش نیست")
        return cleaned
