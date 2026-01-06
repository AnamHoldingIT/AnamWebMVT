# admin_panel/views_worklog.py

import datetime
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from urllib.parse import urlencode

import jdatetime
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch, Q, OuterRef, Exists
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, DetailView
from worklog.models import DailyPlan, DailyReport, Project, ProjectMember, ReportAchievement, ReportStatus
from .mixins import AdminRequiredMixin

User = apps.get_model(settings.AUTH_USER_MODEL)

# ----------------------------
# Constants
# ----------------------------

UI_AVATAR_BASE = "https://ui-avatars.com/api/"
AVATAR_BG_MANAGER = "C5A059"
AVATAR_BG_MEMBER = "333"
AVATAR_COLOR_MANAGER = "000"
AVATAR_COLOR_MEMBER = "fff"

PERSIAN_MONTHS = {
    1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
    5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
    9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند",
}


# ----------------------------
# Helpers
# ----------------------------

def user_display_name(user) -> str:
    """نمایش نام کاربر مطابق مدل شما."""
    return (getattr(user, "full_name", "") or getattr(user, "username", "") or "User").strip()


def ui_avatar_url(name: str, is_manager: bool) -> str:
    """ساخت آدرس آواتار با رنگ‌بندی مدیر/عضو."""
    safe = name.replace(" ", "+")
    if is_manager:
        return f"{UI_AVATAR_BASE}?name={safe}&background={AVATAR_BG_MANAGER}&color={AVATAR_COLOR_MANAGER}"
    return f"{UI_AVATAR_BASE}?name={safe}&background={AVATAR_BG_MEMBER}&color={AVATAR_COLOR_MEMBER}"


def jalali_date_str(g_date) -> str:
    """YYYY/MM/DD (انگلیسی) از date میلادی."""
    if not g_date:
        return ""
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{j.year:04d}/{j.month:02d}/{j.day:02d}"


def fa_to_en_digits(value: str) -> str:
    if not value:
        return ""
    fa = "۰۱۲۳۴۵۶۷۸۹"
    ar = "٠١٢٣٤٥٦٧٨٩"
    out = []
    for ch in str(value):
        if ch in fa:
            out.append(str(fa.index(ch)))
        elif ch in ar:
            out.append(str(ar.index(ch)))
        else:
            out.append(ch)
    return "".join(out)


def to_persian_digits(value) -> str:
    if value is None:
        return ""
    en = "0123456789"
    fa = "۰۱۲۳۴۵۶۷۸۹"
    return str(value).translate(str.maketrans({en[i]: fa[i] for i in range(10)}))


def parse_jalali_to_gregorian(date_j: str):
    """
    '۱۴۰۴/۰۹/۰۱' یا '1404/09/01' => date میلادی
    """
    if not date_j:
        return None
    v = fa_to_en_digits(date_j).strip().replace("-", "/")
    parts = v.split("/")
    if len(parts) != 3:
        return None
    try:
        jy, jm, jd = map(int, parts)
        return jdatetime.date(jy, jm, jd).togregorian()
    except Exception:
        return None


def jalali_human_from_gregorian(g_date) -> str:
    """'۱ آذر ۱۴۰۴'"""
    if not g_date:
        return ""
    j = jdatetime.date.fromgregorian(date=g_date)
    return f"{to_persian_digits(j.day)} {PERSIAN_MONTHS.get(j.month, '')} {to_persian_digits(j.year)}"


def jalali_compact_from_gregorian(g_date) -> str:
    """'۱۴۰۴/۰۹/۰۱'"""
    if not g_date:
        return ""
    j = jdatetime.date.fromgregorian(date=g_date)
    s = f"{j.year:04d}/{j.month:02d}/{j.day:02d}"
    return to_persian_digits(s)


def user_role_label(user) -> str:
    """Label نقش کاربر (اگر get_role_display داشت)."""
    if hasattr(user, "get_role_display"):
        try:
            return user.get_role_display() or ""
        except Exception:
            pass
    return getattr(user, "role", "") or ""


def get_ui_avatar(name):
    """تولید لینک آواتار بر اساس نام"""
    safe_name = str(name).replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={safe_name}&background=C5A059&color=000"


def jalali_pretty(date_obj):
    """نمایش تاریخ به صورت: ۲۵ آذر ۱۴۰۲"""
    if not date_obj: return ""
    j = jdatetime.date.fromgregorian(date=date_obj)
    months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    return f"{j.day} {months[j.month - 1]} {j.year}"


def to_persian_digits(value):
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


# ----------------------------
# DTOs
# ----------------------------

@dataclass
class AvatarItem:
    title: str
    url: str
    is_manager: bool = False


@dataclass
class MemberRow:
    id: int
    user_id: int
    name: str
    email: str
    role: str
    is_manager: bool
    avatar_url: str


@dataclass
class DailyRow:
    index: int
    user_id: int
    user_name: str
    user_role: str
    avatar_url: str
    is_manager: bool
    status_key: str  # planned | waiting | done | absent
    status_label: str
    is_inactive: bool
    plan_id: Optional[int] = None


# ----------------------------
# Worklog - Projects List (ListView)
# ----------------------------

class AdminWorklogProjectListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/worklog/project_list.html"
    model = Project
    paginate_by = 10
    context_object_name = "projects"

    def get_queryset(self):
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "all").strip()  # all|active|archived

        members_qs = (
            ProjectMember.objects
            .select_related("user")
            .order_by("id")
        )

        qs = (
            Project.objects
            .prefetch_related(Prefetch("members", queryset=members_qs, to_attr="pref_members"))
            .order_by("-created_at")
        )

        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "archived":
            qs = qs.filter(is_active=False)

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(sheet_url__icontains=q))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "all").strip()

        page_obj = ctx.get("page_obj")
        rows: List[dict] = []

        start_index = ((page_obj.number - 1) * self.paginate_by) if page_obj else 0
        page_list = page_obj.object_list if page_obj else []

        for i, project in enumerate(page_list, start=1):
            pref_members: List[ProjectMember] = getattr(project, "pref_members", []) or []

            managers = [m for m in pref_members if m.role == ProjectMember.ROLE_MANAGER]
            others = [m for m in pref_members if m.role != ProjectMember.ROLE_MANAGER]
            ordered = managers + others

            shown = ordered[:4]
            remaining_count = max(0, len(ordered) - len(shown))

            avatars: List[AvatarItem] = []
            for m in shown:
                u = m.user
                name = user_display_name(u)
                is_mgr = (m.role == ProjectMember.ROLE_MANAGER)
                avatars.append(
                    AvatarItem(
                        title=f"{name} (مدیر)" if is_mgr else name,
                        url=ui_avatar_url(name, is_mgr),
                        is_manager=is_mgr,
                    )
                )

            rows.append({
                "index": start_index + i,
                "id": project.id,
                "title": project.title,
                "is_active": project.is_active,
                "sheet_url": project.sheet_url,
                "created_jalali": jalali_date_str(project.created_at.date() if project.created_at else None),
                "avatars": avatars,
                "remaining_count": remaining_count,
                "team_is_grayscale": (not project.is_active),
            })

        ctx.update({
            "q": q,
            "status": status,
            "rows": rows,
            "total_count": ctx["paginator"].count if ctx.get("paginator") else 0,
            "showing_from": (start_index + 1) if rows else 0,
            "showing_to": (start_index + len(rows)) if rows else 0,
        })
        return ctx

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        action = (request.POST.get("action") or "").strip()  # archive | restore

        try:
            project_id = int(request.POST.get("project_id"))
        except Exception:
            messages.error(request, "شناسه پروژه نامعتبر است.")
            return redirect("admin_panel:worklog_projects")

        project = Project.objects.filter(id=project_id).first()
        if not project:
            messages.error(request, "پروژه یافت نشد.")
            return redirect("admin_panel:worklog_projects")

        if action == "archive":
            project.is_active = False
            project.save(update_fields=["is_active"])
            messages.success(request, "پروژه آرشیو شد.")
        elif action == "restore":
            project.is_active = True
            project.save(update_fields=["is_active"])
            messages.success(request, "پروژه بازگردانی شد.")
        else:
            messages.error(request, "عملیات نامعتبر است.")

        # ✅ برگرد دقیقاً به همان صفحه/فیلتر (بدون تغییر HTML)
        return redirect(request.META.get("HTTP_REFERER") or reverse("admin_panel:worklog_projects"))


# ----------------------------
# Worklog - Project Edit (TemplateView kept to avoid bugs)
# ----------------------------

class AdminWorklogProjectUpdateView(AdminRequiredMixin, TemplateView):
    template_name = "admin-panel/worklog/project_edit.html"

    def _get_project(self, pk: int) -> Project:
        project = (
            Project.objects
            .prefetch_related(
                Prefetch(
                    "members",
                    queryset=ProjectMember.objects.select_related("user").order_by("id"),
                    to_attr="pref_members",
                )
            )
            .filter(pk=pk)
            .first()
        )
        if not project:
            raise Http404("پروژه یافت نشد.")
        return project

    def _build_members(self, project: Project) -> List[MemberRow]:
        members: List[ProjectMember] = getattr(project, "pref_members", []) or []

        managers = [m for m in members if m.role == ProjectMember.ROLE_MANAGER]
        others = [m for m in members if m.role != ProjectMember.ROLE_MANAGER]
        ordered = managers + others

        rows: List[MemberRow] = []
        for m in ordered:
            u = m.user
            name = user_display_name(u)
            is_mgr = (m.role == ProjectMember.ROLE_MANAGER)

            rows.append(MemberRow(
                id=m.id,
                user_id=u.id,
                name=name,
                email=u.email or "",
                role=m.role,
                is_manager=is_mgr,
                avatar_url=ui_avatar_url(name, is_mgr),
            ))
        return rows

    def _available_users(self, project: Project):
        existing_user_ids = [m.user_id for m in getattr(project, "pref_members", []) or []]
        return (
            User.objects
            .filter(is_active=True)
            .exclude(id__in=existing_user_ids)
            .order_by("-date_joined")[:200]
        )

    def get(self, request, pk: int, *args, **kwargs):
        project = self._get_project(pk)
        ctx = {
            "project": project,
            "back_url": reverse("admin_panel:worklog_projects"),
            "members": self._build_members(project),
            "members_count": len(getattr(project, "pref_members", []) or []),
            "available_users": self._available_users(project),
            "ROLE_MEMBER": ProjectMember.ROLE_MEMBER,
            "ROLE_MANAGER": ProjectMember.ROLE_MANAGER,
        }
        return self.render_to_response(ctx)

    @transaction.atomic
    def post(self, request, pk: int, *args, **kwargs):
        project = self._get_project(pk)

        # --- 1) ذخیره تنظیمات عمومی + نقش‌ها ---
        if "save_project" in request.POST:
            title = (request.POST.get("title") or "").strip()
            sheet_url = (request.POST.get("sheet_url") or "").strip()
            is_active = (request.POST.get("is_active") == "on")

            if not title:
                messages.error(request, "عنوان پروژه الزامی است.")
                return redirect("admin_panel:worklog_project_edit", pk=pk)

            project.title = title
            project.sheet_url = sheet_url
            project.is_active = is_active
            project.save(update_fields=["title", "sheet_url", "is_active"])

            members = list(ProjectMember.objects.filter(project=project))
            member_map = {m.id: m for m in members}

            changed = []
            for key, val in request.POST.items():
                if not key.startswith("role_"):
                    continue
                try:
                    mid = int(key.split("_")[1])
                except Exception:
                    continue

                if mid in member_map and val in (ProjectMember.ROLE_MEMBER, ProjectMember.ROLE_MANAGER):
                    m = member_map[mid]
                    if m.role != val:
                        m.role = val
                        changed.append(m)

            if changed:
                ProjectMember.objects.bulk_update(changed, ["role"])

            messages.success(request, "تغییرات پروژه ذخیره شد.")
            return redirect("admin_panel:worklog_project_edit", pk=pk)

        # --- 2) افزودن عضو ---
        if "add_member" in request.POST:
            user_id = request.POST.get("new_user_id")
            role = request.POST.get("new_role") or ProjectMember.ROLE_MEMBER

            try:
                user_id_int = int(user_id)
            except Exception:
                messages.error(request, "کاربر معتبر انتخاب کنید.")
                return redirect("admin_panel:worklog_project_edit", pk=pk)

            if role not in (ProjectMember.ROLE_MEMBER, ProjectMember.ROLE_MANAGER):
                role = ProjectMember.ROLE_MEMBER

            user = User.objects.filter(id=user_id_int, is_active=True).first()
            if not user:
                messages.error(request, "کاربر یافت نشد.")
                return redirect("admin_panel:worklog_project_edit", pk=pk)

            obj, created = ProjectMember.objects.get_or_create(
                project=project,
                user=user,
                defaults={"role": role, "is_active": True},
            )

            if not created:
                updated = False
                if not obj.is_active:
                    obj.is_active = True
                    updated = True
                if obj.role != role:
                    obj.role = role
                    updated = True
                if updated:
                    obj.save(update_fields=["is_active", "role"])
                messages.info(request, "این کاربر از قبل عضو پروژه بوده؛ بروزرسانی شد.")
            else:
                messages.success(request, "عضو جدید اضافه شد.")

            return redirect("admin_panel:worklog_project_edit", pk=pk)

        # --- 3) حذف عضو ---
        if "remove_member" in request.POST:
            try:
                member_id = int(request.POST.get("remove_member"))
            except Exception:
                messages.error(request, "درخواست حذف نامعتبر است.")
                return redirect("admin_panel:worklog_project_edit", pk=pk)

            member = ProjectMember.objects.filter(id=member_id, project=project).first()
            if not member:
                messages.error(request, "عضو یافت نشد.")
                return redirect("admin_panel:worklog_project_edit", pk=pk)

            if member.role == ProjectMember.ROLE_MANAGER:
                mgr_count = ProjectMember.objects.filter(
                    project=project,
                    role=ProjectMember.ROLE_MANAGER,
                    is_active=True
                ).count()
                if mgr_count <= 1:
                    messages.error(request, "حداقل یک مدیر پروژه باید باقی بماند.")
                    return redirect("admin_panel:worklog_project_edit", pk=pk)

            member.delete()
            messages.success(request, "عضو از پروژه حذف شد.")
            return redirect("admin_panel:worklog_project_edit", pk=pk)

        return redirect("admin_panel:worklog_project_edit", pk=pk)


# ----------------------------
# Worklog - Project Create (CreateView)
# ----------------------------

class AdminWorklogProjectCreateView(AdminRequiredMixin, CreateView):
    """
    تبدیل از TemplateView به CreateView
    بدون تغییر رفتار: همچنان از request.POST دستی می‌خواند و همان تمپلیت را رندر می‌کند.
    """
    template_name = "admin-panel/worklog/project_create.html"
    model = Project
    fields: List[str] = []  # چون دستی می‌سازیم (ModelForm استفاده نمی‌کنیم)

    def get_available_users(self):
        return (
            User.objects
            .filter(is_active=True)
            .only("id", "username", "full_name")
            .order_by("-date_joined")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "back_url": reverse("admin_panel:worklog_projects"),
            "available_users": self.get_available_users(),
            "ROLE_MEMBER": ProjectMember.ROLE_MEMBER,
            "ROLE_MANAGER": ProjectMember.ROLE_MANAGER,
        })
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        title = (request.POST.get("title") or "").strip()
        sheet_url = (request.POST.get("sheet_url") or "").strip()
        is_active = (request.POST.get("is_active") == "on")

        if not title:
            messages.error(request, "عنوان پروژه الزامی است.")
            return redirect("admin_panel:worklog_project_create")

        if not sheet_url:
            messages.error(request, "لینک گوگل شیت الزامی است.")
            return redirect("admin_panel:worklog_project_create")

        project = Project.objects.create(
            title=title,
            sheet_url=sheet_url,
            is_active=is_active,
        )

        user_ids = request.POST.getlist("member_user_id")
        roles = request.POST.getlist("member_role")

        seen: Set[int] = set()
        bulk: List[ProjectMember] = []

        for uid, role in zip(user_ids, roles):
            try:
                uid_int = int(uid)
            except ValueError:
                continue

            if uid_int in seen:
                continue
            seen.add(uid_int)

            if role not in (ProjectMember.ROLE_MEMBER, ProjectMember.ROLE_MANAGER):
                role = ProjectMember.ROLE_MEMBER

            user = User.objects.filter(id=uid_int, is_active=True).first()
            if not user:
                continue

            bulk.append(ProjectMember(
                project=project,
                user=user,
                role=role,
                is_active=True,
            ))

        if bulk:
            ProjectMember.objects.bulk_create(bulk)

        messages.success(request, "پروژه با موفقیت ساخته شد.")
        return redirect("admin_panel:worklog_project_edit", pk=project.id)


# ----------------------------
# Worklog - Plans List (kept TemplateView)
# ----------------------------

class AdminWorklogPlansListView(AdminRequiredMixin, TemplateView):
    template_name = "admin-panel/worklog/admin_plans_list.html"
    paginate_by = 5

    def _status(self, selected_date, today, has_plan: bool, has_report: bool):
        if not has_plan:
            return "absent", "ثبت نشده"
        if selected_date > today:
            return "planned", "برنامه‌ریزی شده"
        if has_report:
            return "done", "تکمیل شده"
        return "waiting", "منتظر گزارش"

    def _clean_date_j(self, raw: str) -> str:
        if not raw:
            return ""
        s = str(raw)
        s = s.replace("%2F", "/").replace("%2f", "/")
        s = fa_to_en_digits(s)
        s = s.replace("-", "/").replace("\\", "/")
        s = s.replace("\u200c", "").replace(" ", "")
        s = re.sub(r"[^0-9/]", "", s)

        m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
        if not m:
            return ""
        y, mo, d = m.groups()
        y = int(y);
        mo = int(mo);
        d = int(d)
        if not (1200 <= y <= 1600): return ""
        if not (1 <= mo <= 12): return ""
        if not (1 <= d <= 31): return ""
        return f"{y:04d}/{mo:02d}/{d:02d}"

    def _compute_stats(self, users_qs, selected_g, today) -> Dict[str, int]:
        user_ids = list(users_qs.values_list("id", flat=True))
        if not user_ids:
            return {"total": 0, "done": 0, "waiting": 0, "planned": 0, "absent": 0}

        memberships = list(
            ProjectMember.objects
            .filter(user_id__in=user_ids, is_active=True, user__is_active=True)
            .values("id", "user_id")
        )
        mem_ids = [m["id"] for m in memberships]
        if not mem_ids:
            return {"total": len(user_ids), "done": 0, "waiting": 0, "planned": 0, "absent": len(user_ids)}

        plans = list(
            DailyPlan.objects
            .filter(project_member_id__in=mem_ids, date=selected_g)
            .values("id", "project_member_id")
        )
        plan_ids = [p["id"] for p in plans]

        report_plan_ids: Set[int] = set()
        if plan_ids:
            report_plan_ids = set(
                DailyReport.objects.filter(plan_id__in=plan_ids).values_list("plan_id", flat=True)
            )

        mem_has_plan = {p["project_member_id"] for p in plans}
        plan_by_mem = {p["project_member_id"]: p["id"] for p in plans}

        user_has_plan = {uid: False for uid in user_ids}
        user_has_report = {uid: False for uid in user_ids}

        for m in memberships:
            uid = m["user_id"]
            mid = m["id"]
            if mid in mem_has_plan:
                user_has_plan[uid] = True
            pid = plan_by_mem.get(mid)
            if pid and pid in report_plan_ids:
                user_has_report[uid] = True

        done = waiting = planned = absent = 0
        for uid in user_ids:
            sk, _ = self._status(selected_g, today, user_has_plan.get(uid, False), user_has_report.get(uid, False))
            if sk == "done":
                done += 1
            elif sk == "waiting":
                waiting += 1
            elif sk == "planned":
                planned += 1
            else:
                absent += 1

        return {"total": len(user_ids), "done": done, "waiting": waiting, "planned": planned, "absent": absent}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        req = self.request

        q = (req.GET.get("q") or "").strip()
        user_id = (req.GET.get("user") or "").strip()
        status = (req.GET.get("status") or "").strip()
        nav = (req.GET.get("nav") or "").strip()
        page = req.GET.get("page") or 1

        today = timezone.localdate()

        raw_date_clean = self._clean_date_j(req.GET.get("date_j") or "")
        selected_from_picker = parse_jalali_to_gregorian(raw_date_clean) if raw_date_clean else None

        if (req.GET.get("date_j") and not selected_from_picker):
            messages.error(req, "تاریخ انتخاب‌شده نامعتبر است. دوباره انتخاب کنید.")

        base_g = selected_from_picker or today

        if nav == "today":
            selected_g = today
        elif nav == "prev":
            selected_g = base_g - datetime.timedelta(days=1)
        elif nav == "next":
            selected_g = base_g + datetime.timedelta(days=1)
        else:
            selected_g = base_g

        date_j_display = jalali_compact_from_gregorian(selected_g)
        date_title = jalali_human_from_gregorian(selected_g)

        # ---------------------------
        # 1) Query پایه (بدون status)
        # ---------------------------
        base_users_qs = (
            User.objects
            .filter(is_active=True, project_memberships__is_active=True)
            .distinct()
            .only("id", "username", "full_name", "role")
            .order_by("-date_joined")
        )

        if user_id.isdigit():
            base_users_qs = base_users_qs.filter(id=int(user_id))

        if q:
            base_users_qs = base_users_qs.filter(Q(username__icontains=q) | Q(full_name__icontains=q))

        # آمار رو از base بگیر (مثل قبل خراب نشه)
        stats = self._compute_stats(base_users_qs, selected_g, today)

        # ---------------------------
        # 2) status filter قبل از pagination (حل مشکل اصلی)
        # ---------------------------
        users_for_list = base_users_qs

        if status:
            plan_exists = DailyPlan.objects.filter(
                date=selected_g,
                project_member__user_id=OuterRef("pk"),
                project_member__is_active=True,
                project_member__user__is_active=True,
            )
            report_exists = DailyReport.objects.filter(
                plan__date=selected_g,
                plan__project_member__user_id=OuterRef("pk"),
                plan__project_member__is_active=True,
                plan__project_member__user__is_active=True,
            )

            users_for_list = users_for_list.annotate(
                _has_plan=Exists(plan_exists),
                _has_report=Exists(report_exists),
            )

            if status == "absent":
                users_for_list = users_for_list.filter(_has_plan=False)
            elif status == "planned":
                users_for_list = users_for_list.filter(_has_plan=True) if selected_g > today else users_for_list.none()
            elif status == "done":
                users_for_list = users_for_list.filter(
                    _has_report=True) if selected_g <= today else users_for_list.none()
            elif status == "waiting":
                if selected_g <= today:
                    users_for_list = users_for_list.filter(_has_plan=True, _has_report=False)
                else:
                    users_for_list = users_for_list.none()

        paginator = Paginator(users_for_list, self.paginate_by)
        page_obj = paginator.get_page(page)

        page_user_ids = list(page_obj.object_list.values_list("id", flat=True))

        memberships = list(
            ProjectMember.objects
            .filter(user_id__in=page_user_ids, is_active=True, user__is_active=True)
            .values("id", "user_id", "role")
        )
        mem_ids = [m["id"] for m in memberships]

        plans = list(
            DailyPlan.objects
            .filter(project_member_id__in=mem_ids, date=selected_g)
            .values("id", "project_member_id")
        )
        plan_ids = [p["id"] for p in plans]

        report_plan_ids: Set[int] = set()
        if plan_ids:
            report_plan_ids = set(
                DailyReport.objects.filter(plan_id__in=plan_ids).values_list("plan_id", flat=True)
            )

        plan_by_mem = {p["project_member_id"]: p["id"] for p in plans}
        mem_has_plan = set(plan_by_mem.keys())

        user_has_plan = {uid: False for uid in page_user_ids}
        user_has_report = {uid: False for uid in page_user_ids}
        user_is_manager = {uid: False for uid in page_user_ids}
        user_plan_id: Dict[int, Optional[int]] = {uid: None for uid in page_user_ids}

        for m in memberships:
            uid = m["user_id"]
            mid = m["id"]

            if m["role"] == ProjectMember.ROLE_MANAGER:
                user_is_manager[uid] = True

            pid = plan_by_mem.get(mid)

            if mid in mem_has_plan:
                user_has_plan[uid] = True

            if pid:
                user_plan_id[uid] = max(user_plan_id[uid] or 0, pid)
                if pid in report_plan_ids:
                    user_has_report[uid] = True

        rows: List[DailyRow] = []
        start_index = (page_obj.number - 1) * self.paginate_by

        visible_index = 0
        for u in page_obj.object_list:
            uid = u.id
            name = user_display_name(u)
            is_mgr = user_is_manager.get(uid, False)

            sk, sl = self._status(
                selected_g,
                today,
                user_has_plan.get(uid, False),
                user_has_report.get(uid, False),
            )

            visible_index += 1
            rows.append(DailyRow(
                index=start_index + visible_index,
                user_id=uid,
                user_name=name,
                user_role=user_role_label(u),
                avatar_url=ui_avatar_url(name, is_mgr),
                is_manager=is_mgr,
                status_key=sk,
                status_label=sl,
                is_inactive=(sk == "absent"),
                plan_id=user_plan_id.get(uid),
            ))

        # querystring برای pagination (بدون nav و بدون page)
        params = {}
        if date_j_display: params["date_j"] = date_j_display
        if q: params["q"] = q
        if user_id: params["user"] = user_id
        if status: params["status"] = status
        query_params = urlencode(params)

        ctx.update({
            "q": q,
            "user_id": user_id,
            "status": status,
            "date_j": date_j_display,
            "selected_date_title": date_title,

            "rows": rows,
            "page_obj": page_obj,
            "is_paginated": page_obj.paginator.num_pages > 1,
            "query_params": query_params,

            "stat_total": stats["total"],
            "stat_done": stats["done"],
            "stat_waiting": stats["waiting"],
            "stat_absent": stats["absent"],
        })
        return ctx


def jalali_human_from_dt(dt) -> str:
    """ '۲۴ آذر ۱۴۰۴ - ۲۲:۳۰' """
    if not dt:
        return ""
    g_date = dt.date()
    j = jdatetime.date.fromgregorian(date=g_date)
    hh = to_persian_digits(f"{dt.hour:02d}")
    mm = to_persian_digits(f"{dt.minute:02d}")
    return f"{to_persian_digits(j.day)} {PERSIAN_MONTHS.get(j.month, '')} {to_persian_digits(j.year)} - {hh}:{mm}"


# ----------------------------
# Detail View
# ----------------------------
class AdminDailyPlanDetailView(AdminRequiredMixin, DetailView):
    model = DailyPlan
    template_name = "admin-panel/worklog/admin_plan_detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        # جلوگیری از کوئری‌های اضافی (N+1)
        return DailyPlan.objects.select_related(
            'project_member__user',
            'project_member__project'
        ).prefetch_related(
            'achievements',  # اهداف تعریف شده
            'schedule_blocks',  # زمان‌بندی‌ها
            'reports'  # گزارش‌های مرتبط
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        plan = self.object
        user = plan.project_member.user

        # 1. نام و آواتار کاربر
        user_name = getattr(user, 'full_name', user.username) or user.username
        ctx['user_name'] = user_name
        ctx['user_avatar'] = get_ui_avatar(user_name)
        ctx['project_name'] = plan.project_member.project.title

        # 2. تبدیل تاریخ‌ها به شمسی و فارسی
        ctx['date_pretty'] = to_persian_digits(jalali_pretty(plan.date))
        ctx['created_at_pretty'] = to_persian_digits(jalali_pretty(plan.created_at.date()))

        # 3. بررسی وضعیت اهداف (Achievements)
        # اگر گزارشی برای این پلن ثبت شده باشد، وضعیت تیک خوردن اهداف را می‌کشیم
        last_report = plan.reports.last()  # فرض می‌کنیم آخرین گزارش ملاک است
        achieved_ids = set()

        if last_report:
            # شناسه اهدافی که در گزارش تیک خورده‌اند (achieved=True)
            achieved_ids = set(
                ReportAchievement.objects.filter(
                    report=last_report,
                    achieved=True
                ).values_list('achievement_id', flat=True)
            )

        # ساخت لیست نهایی اهداف برای نمایش در تمپلیت
        achievements_list = []
        for ach in plan.achievements.all():
            achievements_list.append({
                'title': ach.title,
                'is_done': (ach.id in achieved_ids) if last_report else False,
                'has_report': bool(last_report)  # برای اینکه بدانیم کلا گزارشی هست یا نه
            })
        ctx['achievements_display'] = achievements_list

        # 4. آماده‌سازی بلاک‌های زمانی (مرتب شده)
        # تبدیل اعداد ساعت به فارسی
        schedule_list = []
        for block in plan.schedule_blocks.order_by('start_time'):
            s_time = block.start_time.strftime("%H:%M")
            e_time = block.end_time.strftime("%H:%M")
            schedule_list.append({
                'start': to_persian_digits(s_time),
                'end': to_persian_digits(e_time),
                'title': block.task_title,
                'desc': block.description,
                'is_required': block.is_required,
            })
        ctx['schedule_display'] = schedule_list

        return ctx


class AdminWorklogReportListView(AdminRequiredMixin, TemplateView):
    template_name = "admin-panel/worklog/report_list.html"
    paginate_by = 5

    def _clean_date_j(self, raw: str) -> str:
        if not raw:
            return ""
        s = str(raw).replace("%2F", "/").replace("%2f", "/")
        s = fa_to_en_digits(s).replace("-", "/").replace("\\", "/")
        s = s.replace("\u200c", "").replace(" ", "")
        import re
        s = re.sub(r"[^0-9/]", "", s)
        m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
        if not m:
            return ""
        y, mo, d = map(int, m.groups())
        if not (1200 <= y <= 1600 and 1 <= mo <= 12 and 1 <= d <= 31):
            return ""
        return f"{y:04d}/{mo:02d}/{d:02d}"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        req = self.request

        q = (req.GET.get("q") or "").strip()
        filter_status = (req.GET.get("status") or "").strip()
        nav = (req.GET.get("nav") or "").strip()
        page = int(req.GET.get("page") or 1)

        today = timezone.localdate()

        # ---- date ----
        raw_date_clean = self._clean_date_j(req.GET.get("date_j") or "")
        selected_from_picker = parse_jalali_to_gregorian(raw_date_clean) if raw_date_clean else None
        base_g = selected_from_picker or today

        if nav == "today":
            selected_g = today
        elif nav == "prev":
            selected_g = base_g - datetime.timedelta(days=1)
        elif nav == "next":
            selected_g = base_g + datetime.timedelta(days=1)
        else:
            selected_g = base_g

        date_j_display = jalali_compact_from_gregorian(selected_g)
        date_title = jalali_human_from_gregorian(selected_g)

        # ---- base users ----
        users_base = (
            User.objects
            .filter(is_active=True, project_memberships__is_active=True)
            .distinct()
            .only("id", "username", "full_name", "role", "date_joined")
            .order_by("-date_joined")
        )

        if q:
            users_base = users_base.filter(
                Q(full_name__icontains=q) | Q(username__icontains=q)
            )

        # ---- annotate has_report (برای همین تاریخ) ----
        report_exists_qs = DailyReport.objects.filter(
            date=selected_g,
            project_member__user_id=OuterRef("pk")
        )
        users_base = users_base.annotate(has_report=Exists(report_exists_qs))

        # ---- stats (همه‌ی یوزرها بعد از q، مستقل از status filter) ----
        total = users_base.count()
        registered = users_base.filter(has_report=True).count()

        if selected_g < today:
            waiting = 0
            not_registered = total - registered
        else:
            waiting = total - registered
            not_registered = 0

        stats = {
            "total": total,
            "registered": registered,
            "waiting": waiting,
            "not_registered": not_registered,
        }

        # ---- apply status filter BEFORE pagination ----
        users_for_list = users_base

        if filter_status == "registered":
            users_for_list = users_for_list.filter(has_report=True)

        elif filter_status == "waiting":
            if selected_g >= today:
                users_for_list = users_for_list.filter(has_report=False)
            else:
                users_for_list = users_for_list.none()

        elif filter_status == "not_registered":
            if selected_g < today:
                users_for_list = users_for_list.filter(has_report=False)
            else:
                users_for_list = users_for_list.none()

        # ---- paginate ----
        paginator = Paginator(users_for_list, self.paginate_by)
        page_obj = paginator.get_page(page)
        page_user_ids = list(page_obj.object_list.values_list("id", flat=True))

        # ---- fetch reports only for page users ----
        reports_qs = (
            DailyReport.objects
            .filter(date=selected_g, project_member__user_id__in=page_user_ids)
            .select_related("project_member__user")
            .prefetch_related("achievement_states")
            .order_by("project_member__user_id", "-id")
        )

        # اگر برای یک یوزر چند گزارش بود، جدیدترینش بمونه
        report_map = {}
        for r in reports_qs:
            uid = r.project_member.user_id
            if uid not in report_map:
                report_map[uid] = r

        # ---- rows ----
        rows = []
        for user in page_obj.object_list:
            report = report_map.get(user.id)

            row = {
                "user": user,
                "avatar_url": ui_avatar_url(user_display_name(user), False),
                "role_label": user_role_label(user),
                "status_key": "",
                "achievements_done": 0,
                "achievements_total": 0,
                "percent": 0,
                "report_id": report.id if report else None,
            }

            if report:
                row["status_key"] = "registered"

                ach_states = list(report.achievement_states.all())
                done = sum(1 for a in ach_states if a.achieved)
                total_a = len(ach_states)

                row["achievements_done"] = done
                row["achievements_total"] = total_a
                row["percent"] = int((done / total_a) * 100) if total_a > 0 else 100

            else:
                # توی این view: اگه تاریخ گذشته باشه => ثبت نشده، وگرنه => در انتظار
                if selected_g < today:
                    row["status_key"] = "not_registered"
                else:
                    row["status_key"] = "waiting"

            rows.append(row)

        ctx.update({
            "rows": rows,
            "stats": stats,

            "q": q,
            "filter_status": filter_status,

            "date_j": date_j_display,
            "selected_date_title": date_title,

            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": paginator.num_pages > 1,
        })
        return ctx


# Helper function needed inside view file (if not exists)
def clean_date_j_helper(raw):
    if not raw: return ""
    return raw.replace("-", "/").strip()  # و سایر تمیزکاری‌هایی که در فایل قبل داشتیم


class AdminReportDetailView(AdminRequiredMixin, DetailView):
    model = DailyReport
    template_name = "admin-panel/worklog/report_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        # بهینه‌سازی کوئری‌ها
        return DailyReport.objects.select_related(
            'project_member__user',
            'project_member__project',
            'plan'
        ).prefetch_related(
            'entries__schedule_block',  # تسک‌های اصلی
            'extra_actions',  # کارهای اضافه
            'achievement_states__achievement'  # وضعیت اهداف
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report = self.object
        user = report.project_member.user

        # 1. اطلاعات هدر
        ctx['user_name'] = user_display_name(user)
        ctx['user_avatar'] = ui_avatar_url(ctx['user_name'], False)
        ctx['project_title'] = report.project_member.project.title

        # تاریخ و زمان
        ctx['date_pretty'] = jalali_human_from_gregorian(report.date)
        # ساعت ثبت (از created_at یا locked_at)
        time_obj = report.created_at
        ctx['time_pretty'] = f"{to_persian_digits(time_obj.hour):0>2}:{to_persian_digits(time_obj.minute):0>2}"

        # 2. وضعیت کلی (تکمیل شده / ناقص)
        # منطق: اگر تسک بلاک شده دارد یا ناقص -> وضعیت هشدار
        has_block = report.entries.filter(status=ReportStatus.BLOCKED).exists()
        has_partial = report.entries.filter(status=ReportStatus.PARTIAL).exists()

        if has_block:
            ctx['status_label'] = "دارای مانع"
            ctx['status_class'] = "failed"  # قرمز
        elif has_partial:
            ctx['status_label'] = "ناقص"
            ctx['status_class'] = "warning"  # زرد
        else:
            ctx['status_label'] = "تکمیل شده"
            ctx['status_class'] = "success"  # سبز

        # 3. محاسبه کارایی (Achievements)
        ach_states = list(report.achievement_states.all())
        done_ach = sum(1 for a in ach_states if a.achieved)
        total_ach = len(ach_states)
        ctx['efficiency_percent'] = int((done_ach / total_ach * 100)) if total_ach > 0 else 100
        ctx['achievements_display'] = ach_states

        # 4. آماده‌سازی تایم‌لاین (Entries)
        # ترکیب تسک‌های اصلی و کارهای اضافه برای نمایش
        timeline_items = []

        # الف) تسک‌های اصلی (Entries)
        for entry in report.entries.all():
            block = entry.schedule_block
            status_cls = "info"
            status_txt = entry.get_status_display()

            # کلاس‌های رنگی بر اساس وضعیت
            if entry.status == ReportStatus.DONE:
                status_cls = "success"
            elif entry.status == ReportStatus.BLOCKED:
                status_cls = "danger"
            elif entry.status == ReportStatus.IN_PROGRESS:
                status_cls = "info"
            elif entry.status == ReportStatus.PARTIAL:
                status_cls = "warning"

            timeline_items.append({
                'type': 'main',
                'start': to_persian_digits(block.start_time.strftime("%H:%M")),
                'end': to_persian_digits(block.end_time.strftime("%H:%M")),
                'title': block.task_title,
                'desc_plan': block.description,  # توضیحات برنامه
                'note': entry.note,  # توضیحات کاربر (گزارش)
                'status_class': status_cls,  # برای استایل (success, danger, etc)
                'status_text': status_txt,
                'is_blocked': (entry.status == ReportStatus.BLOCKED),
                'sort_time': block.start_time
            })

        # ب) کارهای اضافه (Extra Actions)
        for extra in report.extra_actions.all():
            s_t = extra.start_time.strftime("%H:%M") if extra.start_time else "??"
            e_t = extra.end_time.strftime("%H:%M") if extra.end_time else "??"

            timeline_items.append({
                'type': 'extra',
                'start': to_persian_digits(s_t),
                'end': to_persian_digits(e_t),
                'title': extra.title,
                'desc_plan': "فعالیت خارج از برنامه",
                'note': extra.description,
                'status_class': "warning",  # معمولا کارهای یهویی زرد هستند
                'status_text': "Unplanned",
                'is_blocked': False,
                'sort_time': extra.start_time or datetime.time(23, 59)  # ته لیست
            })

        # مرتب‌سازی بر اساس ساعت شروع
        timeline_items.sort(key=lambda x: x['sort_time'])
        ctx['timeline_items'] = timeline_items

        return ctx


# admin_panel/views_worklog.py
# (کدهای قبلی را نگه دارید و این کلاس را به انتهای فایل اضافه کنید)

class AdminWorklogStatusOverview(AdminRequiredMixin, TemplateView):
    template_name = "admin-panel/worklog/status_overview.html"
    paginate_by = 15  # تعداد ردیف در هر صفحه جدول

    def _clean_date_j(self, raw: str) -> str:
        # همان تابع تمیزکاری تاریخ که در ویوهای قبلی داشتید
        if not raw: return ""
        s = str(raw).replace("%2F", "/").replace("%2f", "/")
        s = fa_to_en_digits(s).replace("-", "/").replace("\\", "/")
        s = s.replace("\u200c", "").replace(" ", "")
        import re
        s = re.sub(r"[^0-9/]", "", s)
        m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
        if not m: return ""
        y, mo, d = map(int, m.groups())
        if not (1200 <= y <= 1600 and 1 <= mo <= 12 and 1 <= d <= 31): return ""
        return f"{y:04d}/{mo:02d}/{d:02d}"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        req = self.request

        # 1. دریافت پارامترها
        q = (req.GET.get("q") or "").strip()
        status_filter = (req.GET.get("status") or "").strip()  # missing_plan | missing_report | all_ok
        nav = (req.GET.get("nav") or "").strip()
        page_num = req.GET.get("page") or 1

        today = timezone.localdate()

        # 2. مدیریت تاریخ
        raw_date_clean = self._clean_date_j(req.GET.get("date_j") or "")
        selected_from_picker = parse_jalali_to_gregorian(raw_date_clean) if raw_date_clean else None
        base_g = selected_from_picker or today

        if nav == "today":
            selected_g = today
        elif nav == "prev":
            selected_g = base_g - datetime.timedelta(days=1)
        elif nav == "next":
            selected_g = base_g + datetime.timedelta(days=1)
        else:
            selected_g = base_g

        date_j_display = jalali_compact_from_gregorian(selected_g)
        date_title = jalali_human_from_gregorian(selected_g)

        # 3. کوئری اصلی کاربران (Active)
        users_qs = User.objects.filter(is_active=True).order_by("-date_joined")

        if q:
            users_qs = users_qs.filter(Q(full_name__icontains=q) | Q(username__icontains=q))

        # 4. Annotate (بررسی وجود پلن و گزارش)
        # توجه: پلن و گزارش به ProjectMember وصل هستند، پس باید از طریق آن چک کنیم.

        has_plan_subquery = DailyPlan.objects.filter(
            project_member__user=OuterRef('pk'),
            date=selected_g
        )

        has_report_subquery = DailyReport.objects.filter(
            project_member__user=OuterRef('pk'),
            date=selected_g
        )

        users_qs = users_qs.annotate(
            has_plan=Exists(has_plan_subquery),
            has_report=Exists(has_report_subquery)
        )

        # 5. اعمال فیلتر وضعیت (اختیاری)
        if status_filter == "missing_plan":
            users_qs = users_qs.filter(has_plan=False)
        elif status_filter == "missing_report":
            users_qs = users_qs.filter(has_report=False)
        elif status_filter == "has_plan":
            users_qs = users_qs.filter(has_plan=True)
        elif status_filter == "has_report":
            users_qs = users_qs.filter(has_report=True)

        # 6. آمار سریع (Stats) برای بالای صفحه (روی کل کوئری فیلتر نشده بر اساس وضعیت)
        # برای آمار دقیق باید یک کوئری جدا بدون فیلتر status بزنیم یا همین را قبل فیلتر استفاده کنیم.
        # اینجا برای سادگی روی همین لیست فیلتر شده یا کل یوزرها آمار میگیریم:
        total_users = User.objects.filter(is_active=True).count()
        # تعداد کسانی که پلن دارند
        total_plans = User.objects.filter(is_active=True).annotate(
            has_p=Exists(has_plan_subquery)
        ).filter(has_p=True).count()
        # تعداد کسانی که گزارش دارند
        total_reports = User.objects.filter(is_active=True).annotate(
            has_r=Exists(has_report_subquery)
        ).filter(has_r=True).count()

        # 7. صفحه بندی
        paginator = Paginator(users_qs, self.paginate_by)
        page_obj = paginator.get_page(page_num)

        # 8. آماده‌سازی داده برای نمایش
        rows = []
        for user in page_obj.object_list:
            rows.append({
                "user": user,
                "avatar_url": ui_avatar_url(user_display_name(user), False),  # تابع کمکی موجود در فایل
                "role": user_role_label(user),
                "has_plan": user.has_plan,
                "has_report": user.has_report,
            })

        # ساخت کوئری استرینگ برای صفحه بندی
        params = {
            "date_j": date_j_display,
            "q": q,
            "status": status_filter
        }
        query_params = urlencode({k: v for k, v in params.items() if v})

        ctx.update({
            "rows": rows,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "query_params": query_params,

            "date_j": date_j_display,
            "selected_date_title": date_title,
            "q": q,
            "status": status_filter,

            # Stats
            "stat_total": total_users,
            "stat_plans": total_plans,
            "stat_reports": total_reports,
            "stat_missing_plan": total_users - total_plans,
        })

        return ctx
