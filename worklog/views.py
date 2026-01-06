# worklog/views.py
import json
from datetime import timedelta, datetime, time

import jdatetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView

from worklog.forms import DailyPlanForm
from worklog.models import (
    ProjectMember,
    DailyPlan,
    DailyAchievement,
    DailyScheduleBlock,
    DailyReport,
    ReportEntry,
    ReportStatus,
    ReportExtraAction, ReportAchievement,
)

from worklog.locks import is_locked, calc_plan_lock, calc_report_lock
from worklog.validators import assert_plan_editable, assert_report_editable
from worklog.services import (
    get_or_create_today_report,
    sync_report_entries_from_plan,
    ensure_report_editable,
)

# -----------------------------
# UI helpers (Persian date text)
# -----------------------------
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
PERSIAN_MONTHS = {
    1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
    5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
    9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند",
}
PERSIAN_WEEKDAYS = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه‌شنبه",
    4: "چهارشنبه",
    5: "پنجشنبه",
    6: "جمعه",
}


def to_persian_digits(s: str) -> str:
    return str(s).translate(PERSIAN_DIGITS)


def format_remaining(td):
    if td.total_seconds() <= 0:
        return "۰ دقیقه"
    mins = int(td.total_seconds() // 60)
    h = mins // 60
    m = mins % 60
    if h > 0:
        return f"{to_persian_digits(h)} ساعت و {to_persian_digits(m)} دقیقه"
    return f"{to_persian_digits(m)} دقیقه"


def _aware(dt):
    """Safely make a datetime aware if it's naive (prevents localtime errors)."""
    if not dt:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _parse_time_hhmm(v: str):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return datetime.strptime(v, "%H:%M").time()
    except Exception:
        return None


# -----------------------------
# Dashboard
# -----------------------------
class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "users_panel/dashboard_users.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        memberships = (
            ProjectMember.objects
            .select_related("project")
            .filter(user=user, is_active=True, project__is_active=True)
            .order_by("-joined_at")
        )

        today_j = jdatetime.date.today()
        jalali_today = f"{today_j.year}/{today_j.month:02d}/{today_j.day:02d}"

        display_name = user.full_name or user.username

        primary_role = None
        first = memberships.first()
        if first:
            primary_role = first.get_role_display()

        ctx.update({
            "display_name": display_name,
            "jalali_today": jalali_today,
            "projects_count": memberships.count(),
            "recent_memberships": memberships[:5],
            "primary_role": primary_role,
        })
        return ctx


class PlanDeleteView(LoginRequiredMixin, View):
    def post(self, request, plan_id):
        plan = (
            DailyPlan.objects
            .select_related("project_member", "project_member__project")
            .filter(
                id=plan_id,
                project_member__user=request.user,
                project_member__is_active=True,
                project_member__project__is_active=True,
            )
            .first()
        )
        if not plan:
            raise Http404("برنامه یافت نشد یا دسترسی ندارید.")

        today = timezone.localdate()

        # ✅ فقط آینده قابل حذف است
        if plan.date <= today:
            messages.error(request, "فقط برنامه‌های آینده قابل حذف هستند.")
            return redirect("worklog:plans")

        plan.delete()
        messages.success(request, "برنامه‌ی آینده با موفقیت حذف شد.")
        return redirect("worklog:plans")


# -----------------------------
# Projects
# -----------------------------
class UserProjectsView(LoginRequiredMixin, TemplateView):
    template_name = "users_panel/projects_users.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        memberships = (
            ProjectMember.objects
            .select_related("project")
            .filter(
                user=user,
                is_active=True,
                project__is_active=True,
            )
            .order_by("-joined_at")
        )

        projects = []
        for m in memberships:
            joined_j = jdatetime.date.fromgregorian(date=m.joined_at.date())

            projects.append({
                "id": m.project.id,
                "title": m.project.title,
                "description": getattr(m.project, "description", ""),
                "role": m.role,
                "role_label": m.get_role_display(),
                "is_active": m.project.is_active,
                "joined_at": f"{joined_j.year}/{joined_j.month:02d}/{joined_j.day:02d}",
                "sheet_url": m.project.sheet_url,
            })

        ctx.update({"projects": projects})
        return ctx


# -----------------------------
# Plans List
# -----------------------------
class UserPlanListView(LoginRequiredMixin, TemplateView):
    template_name = "users_panel/plan_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        default_member = (
            ProjectMember.objects
            .select_related("project")
            .filter(user=user, is_active=True, project__is_active=True)
            .order_by("-joined_at")
            .first()
        )
        ctx["default_member_id"] = default_member.id if default_member else None

        plans_qs = (
            DailyPlan.objects
            .select_related("project_member", "project_member__project")
            .prefetch_related("achievements", "schedule_blocks")
            .filter(project_member__user=user, project_member__is_active=True)
            .order_by("-date")
        )

        today_g = timezone.localdate()
        plans = []

        for plan in plans_qs:
            if not plan.locked_at:
                plan.locked_at = calc_plan_lock(plan.date)
                plan.save(update_fields=["locked_at"])

            j = jdatetime.date.fromgregorian(date=plan.date)
            weekday = PERSIAN_WEEKDAYS.get(j.weekday(), "")
            day_num = str(j.day).translate(PERSIAN_DIGITS)
            month_name = PERSIAN_MONTHS.get(j.month, "")

            ach_qs = list(plan.achievements.all().order_by("sort_order", "id")[:3])
            ach_list = [a.title for a in ach_qs]
            ach_count = plan.achievements.count()
            today = timezone.localdate()
            has_extra = plan.schedule_blocks.filter(is_required=False).exists()

            plans.append({
                "id": plan.id,
                "is_today": plan.date == today,
                "is_future": plan.date > today,
                "is_today": plan.date == today_g,
                "weekday": weekday,
                "day_num": day_num,
                "month_name": month_name,
                "jalali_full": f"{j.year:04d}-{j.month:02d}-{j.day:02d}",
                "ach_count": str(ach_count).translate(PERSIAN_DIGITS),
                "ach_list": ach_list,
                "has_extra": has_extra,
                "can_edit": not is_locked(plan.locked_at),
            })

        ctx["plans"] = plans
        return ctx


# -----------------------------
# Plan Edit
# -----------------------------
class PlanEditView(LoginRequiredMixin, View):
    template_name = "users_panel/plan_edit.html"

    def _get_plan(self, request, plan_id):
        plan = (
            DailyPlan.objects
            .select_related("project_member", "project_member__project")
            .prefetch_related("schedule_blocks")
            .filter(
                id=plan_id,
                project_member__user=request.user,
                project_member__is_active=True,
                project_member__project__is_active=True,
            )
            .first()
        )
        if not plan:
            raise Http404("برنامه یافت نشد یا دسترسی ندارید.")
        return plan

    def get(self, request, plan_id):
        plan = self._get_plan(request, plan_id)

        try:
            assert_plan_editable(plan)
            locked = False
        except PermissionDenied:
            locked = True

        BlockFormSet = modelformset_factory(
            DailyScheduleBlock,
            fields=("task_title",),
            extra=0,
            can_delete=False,
        )

        qs = plan.schedule_blocks.all().order_by("start_time", "id")
        formset = BlockFormSet(queryset=qs)

        j = jdatetime.date.fromgregorian(date=plan.date)
        ctx = {
            "plan": plan,
            "formset": formset,
            "is_locked": locked,
            "weekday": PERSIAN_WEEKDAYS.get(j.weekday(), ""),
            "day_num": str(j.day).translate(PERSIAN_DIGITS),
            "month_name": PERSIAN_MONTHS.get(j.month, ""),
            "year_num": str(j.year).translate(PERSIAN_DIGITS),
            "back_url": reverse("worklog:plans"),
        }
        return render(request, self.template_name, ctx)

    def post(self, request, plan_id):
        plan = self._get_plan(request, plan_id)

        try:
            assert_plan_editable(plan)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("worklog:plans")

        BlockFormSet = modelformset_factory(
            DailyScheduleBlock,
            fields=("task_title",),
            extra=0,
            can_delete=False,
        )

        qs = plan.schedule_blocks.all().order_by("start_time", "id")
        formset = BlockFormSet(request.POST, queryset=qs)

        if not formset.is_valid():
            messages.error(request, "لطفاً ورودی‌ها را بررسی کنید.")
            j = jdatetime.date.fromgregorian(date=plan.date)
            return render(request, self.template_name, {
                "plan": plan,
                "formset": formset,
                "is_locked": False,
                "weekday": PERSIAN_WEEKDAYS.get(j.weekday(), ""),
                "day_num": str(j.day).translate(PERSIAN_DIGITS),
                "month_name": PERSIAN_MONTHS.get(j.month, ""),
                "year_num": str(j.year).translate(PERSIAN_DIGITS),
                "back_url": reverse("worklog:plans"),
            })

        formset.save()
        messages.success(request, "تغییرات برنامه ذخیره شد.")
        return redirect("worklog:plans")


# -----------------------------
# Plan Wizard (Create)
# -----------------------------
class PlanWizardCreateView(LoginRequiredMixin, FormView):
    template_name = "users_panel/plan_details.html"
    form_class = DailyPlanForm

    def dispatch(self, request, *args, **kwargs):
        self.member = (
            ProjectMember.objects
            .select_related("project")
            .filter(
                id=kwargs.get("member_id"),
                user=request.user,
                is_active=True,
                project__is_active=True,
            )
            .first()
        )
        if not self.member:
            raise Http404("عضویت پروژه یافت نشد یا دسترسی ندارید.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["member"] = self.member
        ctx["back_url"] = reverse("worklog:plans")
        return ctx

    def form_valid(self, form):
        plan_date = form.cleaned_data["jalali_date"]
        locked_at = calc_plan_lock(plan_date)

        plan, created = DailyPlan.objects.get_or_create(
            project_member=self.member,
            date=plan_date,
            defaults={"locked_at": locked_at}
        )

        if not created:
            form.add_error(None, "برای این تاریخ قبلاً برنامه ثبت شده است.")
            return self.form_invalid(form)

        achievements_raw = self.request.POST.get("achievements_json", "[]")
        blocks_raw = self.request.POST.get("blocks_json", "[]")
        extras_raw = self.request.POST.get("extras_json", "[]")

        try:
            achievements = json.loads(achievements_raw) or []
            blocks = json.loads(blocks_raw) or []
            extras = json.loads(extras_raw) or []
        except json.JSONDecodeError:
            form.add_error(None, "اطلاعات برنامه نامعتبر است. دوباره تلاش کنید.")
            plan.delete()
            return self.form_invalid(form)

        bulk_ach = []
        for idx, title in enumerate(achievements):
            title = (title or "").strip()
            if not title:
                continue
            bulk_ach.append(DailyAchievement(plan=plan, title=title, sort_order=idx))
        if bulk_ach:
            DailyAchievement.objects.bulk_create(bulk_ach)

        bulk_blocks = []

        for b in blocks:
            st = (b.get("start") or "").strip()
            en = (b.get("end") or "").strip()
            tt = (b.get("title") or "").strip()
            ds = (b.get("desc") or "").strip()
            if not (st and en and tt):
                continue
            bulk_blocks.append(DailyScheduleBlock(
                plan=plan,
                start_time=st,
                end_time=en,
                task_title=tt,
                description=ds,
                is_required=True,
            ))

        for b in extras:
            st = (b.get("start") or "").strip()
            en = (b.get("end") or "").strip()
            tt = (b.get("title") or "").strip()
            ds = (b.get("desc") or "").strip()
            if not (st and en and tt):
                continue
            bulk_blocks.append(DailyScheduleBlock(
                plan=plan,
                start_time=st,
                end_time=en,
                task_title=tt,
                description=ds,
                is_required=False,
            ))

        if bulk_blocks:
            DailyScheduleBlock.objects.bulk_create(bulk_blocks)

        return redirect("worklog:plans")


# -----------------------------
# Reports List
# -----------------------------
class UserReportListView(LoginRequiredMixin, TemplateView):
    template_name = "users_panel/report_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        plans_qs = (
            DailyPlan.objects
            .select_related("project_member", "project_member__project")
            .prefetch_related("achievements")
            .filter(project_member__user=user, project_member__is_active=True)
            .order_by("-date")
        )

        today = timezone.localdate()
        now = timezone.localtime(timezone.now())

        report_map = {
            r.date: r
            for r in DailyReport.objects.filter(
                project_member__user=user,
                project_member__is_active=True,
            )
        }

        reports = []
        priority = None
        today_locked_at_iso = ""
        today_now_iso = timezone.localtime(timezone.now()).isoformat()

        for plan in plans_qs:
            j = jdatetime.date.fromgregorian(date=plan.date)
            day_num = to_persian_digits(j.day)
            month_name = PERSIAN_MONTHS.get(j.month, "")
            weekday = PERSIAN_WEEKDAYS.get(j.weekday(), "")

            existing_report = report_map.get(plan.date)
            is_today = (plan.date == today)

            if plan.date > today:
                status = "future"
            elif existing_report:
                status = "completed"
            elif is_today:
                status = "pending"  # فقط امروز امکان ثبت دارد
            else:
                status = "locked_past"

            item = {
                "plan_id": plan.id,  # ✅ صراحتاً

                "report_id": existing_report.id if existing_report else None,
                "is_today": is_today,
                "status": status,
                "title": f"گزارش {weekday}",
                "day_num": day_num,
                "month_name": month_name,
                "jalali_full": f"{j.year:04d}-{j.month:02d}-{j.day:02d}",
            }

            if is_today:
                ach_count = plan.achievements.count()

                if existing_report and existing_report.locked_at:
                    lock_dt = timezone.localtime(_aware(existing_report.locked_at))
                else:
                    lock_dt = timezone.localtime(calc_report_lock(today))

                remaining = lock_dt - now

                start_day = timezone.make_aware(datetime.combine(today, time(0, 0, 0)))
                total = max((lock_dt - start_day).total_seconds(), 1)
                elapsed = max((now - start_day).total_seconds(), 0)
                progress = int(min(100, max(0, (elapsed / total) * 100)))

                priority = {
                    **item,
                    "ach_count": to_persian_digits(ach_count),
                    "remaining_text": format_remaining(remaining),
                    "progress_percent": progress,
                    "lock_text": f"{to_persian_digits(lock_dt.hour).zfill(2)}:{to_persian_digits(lock_dt.minute).zfill(2)}",
                }

                today_locked_at_iso = lock_dt.isoformat()
            else:
                reports.append(item)

        ctx["today_locked_at_iso"] = today_locked_at_iso
        ctx["today_now_iso"] = today_now_iso
        ctx["priority"] = priority
        ctx["reports"] = reports
        return ctx


# -----------------------------
# Report submit (REAL)
# -----------------------------

class UserReportView(LoginRequiredMixin, View):
    template_name = "users_panel/report.html"

    def _get_plan(self, request, plan_id):
        plan = (
            DailyPlan.objects
            .select_related("project_member", "project_member__project")
            .prefetch_related("achievements", "schedule_blocks")
            .filter(
                id=plan_id,
                project_member__user=request.user,
                project_member__is_active=True,
                project_member__project__is_active=True,
            )
            .first()
        )
        if not plan:
            raise Http404("برنامه یافت نشد یا دسترسی ندارید.")
        return plan

    def get(self, request, plan_id):
        plan = self._get_plan(request, plan_id)
        today = timezone.localdate()

        if plan.date != today:
            messages.error(request, "فقط گزارش مربوط به امروز قابل ثبت است.")
            return redirect("worklog:report_list")

        report, _ = get_or_create_today_report(plan.project_member, plan)
        sync_report_entries_from_plan(report)

        for ach in plan.achievements.all():
            ReportAchievement.objects.get_or_create(report=report, achievement=ach)

        locked = False
        try:
            assert_report_editable(report)
        except PermissionDenied:
            locked = True

        j = jdatetime.date.fromgregorian(date=plan.date)

        now = timezone.localtime(timezone.now())
        lock_dt = timezone.localtime(_aware(report.locked_at)) if report.locked_at else None
        remaining_text = format_remaining(lock_dt - now) if lock_dt else ""

        ctx = {
            "plan": plan,
            "report": report,
            "is_locked": locked,
            "weekday": PERSIAN_WEEKDAYS.get(j.weekday(), ""),
            "day_num": to_persian_digits(j.day),
            "month_name": PERSIAN_MONTHS.get(j.month, ""),
            "remaining_text": remaining_text,

            "achievement_states": (
                ReportAchievement.objects
                .select_related("achievement")
                .filter(report=report)
                .order_by("achievement__sort_order", "achievement__id")
            ),
            "entries": (
                ReportEntry.objects
                .select_related("schedule_block")
                .filter(report=report)
                .order_by("schedule_block__start_time", "schedule_block__id")
            ),
            "extras": report.extra_actions.all().order_by("created_at"),
        }
        return render(request, self.template_name, ctx)

    def post(self, request, plan_id):
        plan = self._get_plan(request, plan_id)
        today = timezone.localdate()

        if plan.date != today:
            messages.error(request, "فقط گزارش مربوط به امروز قابل ثبت است.")
            return redirect("worklog:report_list")

        report, _ = get_or_create_today_report(plan.project_member, plan)
        sync_report_entries_from_plan(report)

        # ✅ lock واقعی
        try:
            assert_report_editable(report)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("worklog:report", plan_id=plan.id)

        # -------- save timeline --------
        entries = list(ReportEntry.objects.filter(report=report))
        entry_map = {e.id: e for e in entries}

        for key, val in request.POST.items():
            if key.startswith("status_"):
                try:
                    eid = int(key.split("_")[1])
                    if eid in entry_map:
                        entry_map[eid].status = int(val)
                except Exception:
                    pass

            if key.startswith("note_"):
                try:
                    eid = int(key.split("_")[1])
                    if eid in entry_map:
                        entry_map[eid].note = (val or "").strip()
                except Exception:
                    pass

        if entry_map:
            ReportEntry.objects.bulk_update(entry_map.values(), ["status", "note", "updated_at"])

        # -------- save achievements --------
        ReportAchievement.objects.filter(report=report).update(achieved=False)

        for key in request.POST.keys():
            if key.startswith("ach_"):
                try:
                    aid = int(key.split("_")[1])
                    ReportAchievement.objects.filter(report=report, achievement_id=aid).update(achieved=True)
                except Exception:
                    pass

        # -------- save extras --------
        ReportExtraAction.objects.filter(report=report).delete()

        extras_raw = request.POST.get("extras_json", "[]")
        try:
            extras = json.loads(extras_raw) or []
        except Exception:
            extras = []

        bulk = []
        for ex in extras:
            title = (ex.get("title") or "").strip()
            if not title:
                continue
            bulk.append(
                ReportExtraAction(
                    report=report,
                    title=title,
                    description=(ex.get("desc") or "").strip(),
                    start_time=_parse_time_hhmm(ex.get("start")),
                    end_time=_parse_time_hhmm(ex.get("end")),
                )
            )

        if bulk:
            ReportExtraAction.objects.bulk_create(bulk)

        messages.success(request, "گزارش ذخیره شد.")
        return redirect("worklog:report_list")


class UserReportDetailView(LoginRequiredMixin, View):
    template_name = "users_panel/report_view.html"

    def _get_plan(self, request, plan_id):
        plan = (
            DailyPlan.objects
            .select_related("project_member", "project_member__project")
            .prefetch_related("achievements", "schedule_blocks")
            .filter(
                id=plan_id,
                project_member__user=request.user,
                project_member__is_active=True,
                project_member__project__is_active=True,
            )
            .first()
        )
        if not plan:
            raise Http404("برنامه یافت نشد یا دسترسی ندارید.")
        return plan

    def get(self, request, plan_id):
        plan = self._get_plan(request, plan_id)

        report = (
            DailyReport.objects
            .select_related("plan", "project_member")
            .filter(plan=plan, project_member=plan.project_member, date=plan.date)
            .first()
        )
        if not report:
            messages.error(request, "برای این روز گزارشی ثبت نشده است.")
            return redirect("worklog:report_list")

        # برای نمایشِ درست (اگر entry جا مونده باشه)
        sync_report_entries_from_plan(report)

        # achievements sync (برای نمایش)
        for ach in plan.achievements.all():
            ReportAchievement.objects.get_or_create(report=report, achievement=ach)

        j = jdatetime.date.fromgregorian(date=plan.date)

        ctx = {
            "plan": plan,
            "report": report,

            "day_num": to_persian_digits(j.day),
            "month_name": PERSIAN_MONTHS.get(j.month, ""),
            "weekday": PERSIAN_WEEKDAYS.get(j.weekday(), ""),
            "created_at_text": timezone.localtime(report.created_at).strftime("%Y/%m/%d - %H:%M"),

            "achievement_states": (
                ReportAchievement.objects
                .select_related("achievement")
                .filter(report=report)
                .order_by("achievement__sort_order", "achievement__id")
            ),
            "entries": (
                ReportEntry.objects
                .select_related("schedule_block")
                .filter(report=report)
                .order_by("schedule_block__start_time", "schedule_block__id")
            ),
            "extras": report.extra_actions.all().order_by("created_at"),
        }
        return render(request, self.template_name, ctx)
