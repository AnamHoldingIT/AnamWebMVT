# admin_panel/views.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone

from portfolio.models import PortfolioProject, ProjectCategory, ProjectRole
from .forms import *
from accounts.models import User
from home.models import Contract
from .models import ActivityLog
from home.models import SiteStat
from django.db.models import Q, Count
from zlink.models import ReCode, Referrer


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return (
                user.is_superuser or
                getattr(user, "role", None) == User.ROLE_ADMIN or
                getattr(user, "role", None) == User.ROLE_WATCHER_ADMIN
        )


# 2. این میکسین جدید را می‌سازیم که ادمین بیننده را مسدود می‌کند
class FullAdminRequiredMixin(AdminRequiredMixin):
    def test_func(self):
        # اول شرط کلی (لاگین بودن و استف بودن) چک شود
        is_staff = super().test_func()
        if not is_staff:
            return False

        user = self.request.user
        # اگر کاربر "ادمین بیننده" است، اجازه نده
        if getattr(user, "role", None) == User.ROLE_WATCHER_ADMIN:
            return False

        return True


class DashboardView(FullAdminRequiredMixin, TemplateView):
    template_name = "admin-panel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = timezone.localdate()

        # تعداد کاربر فعال
        stats = SiteStat.get_solo()
        ctx["active_users_count"] = stats.total_views  # 👈 اینجا عدد میره تو همون قالب قبلی

        # تعداد درخواست‌های ثبت‌شده امروز
        ctx["today_new_contracts"] = Contract.objects.filter(
            created_at__date=today
        ).count()

        # تعداد درخواست‌های در وضعیت جدید
        from home.status import STATUS_NEW  # اگه status جدا ساختی
        ctx["pending_contracts_count"] = Contract.objects.filter(
            status=STATUS_NEW
        ).count()

        # فعلاً یه عدد ثابت برای رضایت
        ctx["satisfaction_percent"] = 94

        # آخرین درخواست‌ها (برای جای دیگه اگر خواستی)
        ctx["last_contracts"] = Contract.objects.all()[:5]

        # آخرین فعالیت‌ها
        ctx["latest_activities"] = ActivityLog.objects.select_related("actor")[:10]

        return ctx


class ContractListView(FullAdminRequiredMixin, ListView):
    template_name = "admin-panel/contracts_list.html"
    model = Contract
    context_object_name = "contracts"
    paginate_by = 20


class ContractDetailView(FullAdminRequiredMixin, DetailView):
    template_name = "admin-panel/contract_detail.html"
    model = Contract
    context_object_name = "contract"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # برای ساخت سلکت وضعیت در قالب
        ctx["status_choices"] = Contract._meta.get_field("status").choices
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        new_status = request.POST.get("status")
        valid_statuses = {value for value, _ in Contract._meta.get_field("status").choices}

        if new_status in valid_statuses:
            self.object.status = new_status
            # می‌تونی همین‌جا به عنوان خوانده‌شده هم ست کنی
            if not self.object.is_read:
                self.object.is_read = True
            self.object.save(update_fields=["status", "is_read", "updated_at"])

        return redirect("admin_panel:contract_detail", pk=self.object.pk)


class UserListView(FullAdminRequiredMixin, ListView):
    template_name = "admin-panel/user_list.html"
    model = User
    context_object_name = "users"
    paginate_by = 10
    ordering = "-date_joined"

    def get_queryset(self):
        qs = super().get_queryset()

        q = (self.request.GET.get("q") or "").strip()
        if not q:
            return qs

        # فقط فیلدهایی که واقعاً تو مدل هست
        lookup = (
                Q(username__icontains=q) |
                Q(full_name__icontains=q) |
                Q(email__icontains=q) |
                Q(phone__icontains=q)
        )

        # اگر بعداً فیلد شرکت/استارتاپ اضافه کردی اینجا اضافه میشه
        existing = {f.name for f in User._meta.get_fields() if hasattr(f, "name")}
        for f in ("startup", "startup_name", "company", "company_name"):
            if f in existing:
                lookup |= Q(**{f"{f}__icontains": q})

        return qs.filter(lookup)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = (self.request.GET.get("q") or "").strip()
        return ctx

    def render_to_response(self, context, **response_kwargs):
        is_ajax = self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        if not is_ajax:
            return super().render_to_response(context, **response_kwargs)

        page_obj = context["page_obj"]
        paginator = context["paginator"]

        results = []
        for u in context["users"]:
            results.append({
                "id": u.pk,
                "username": u.username or "",
                "full_name": u.full_name or "",
                "phone": u.phone or "",
                "email": u.email or "",
                "is_superuser": bool(u.is_superuser),
                "role": u.role or "",
            })

        return JsonResponse({
            "results": results,
            "count": paginator.count,
            "page": page_obj.number,
            "num_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
            "prev_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
        })


class UserDetailView(FullAdminRequiredMixin, UpdateView):
    model = User
    template_name = "admin-panel/user_detail.html"
    form_class = UserEditForm
    context_object_name = "user_obj"

    def get_success_url(self):
        return reverse_lazy("admin_panel:user_detail", kwargs={"pk": self.object.pk})


class UserCreateView(FullAdminRequiredMixin, CreateView):
    template_name = "admin-panel/user_create.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("admin_panel:users")


class UserDeleteView(FullAdminRequiredMixin, DeleteView):
    model = User
    template_name = "admin-panel/user_delete_confirm.html"
    success_url = reverse_lazy("admin_panel:users")


class UserResetPasswordView(FullAdminRequiredMixin, FormView):
    template_name = "admin-panel/reset_password.html"
    form_class = ResetPasswordForm

    def form_valid(self, form):
        user = User.objects.get(pk=self.kwargs["pk"])
        user.set_password(form.cleaned_data["password"])
        user.save()
        return redirect("admin_panel:user_detail", pk=user.pk)


class ReCodeListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/recode_list.html"
    model = ReCode
    context_object_name = "recode_list"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("referrer")

        # فیلتر وضعیت
        status = (self.request.GET.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)

        # فیلتر معرف
        ref = (self.request.GET.get("ref") or "").strip()
        if ref:
            qs = qs.filter(referrer__code=ref)

        # جستجو
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(email__icontains=q)
                | Q(city__icontains=q)
                | Q(referrer__name__icontains=q)
                | Q(referrer__code__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        status_field = ReCode._meta.get_field("status")
        ctx["status_choices"] = status_field.choices

        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["query"] = self.request.GET.get("q", "")

        # ✅ معرف‌ها برای دراپ‌داون فیلتر
        ctx["referrers"] = Referrer.objects.filter(is_active=True).order_by("name")
        ctx["current_ref"] = self.request.GET.get("ref", "")

        return ctx


class ReCodeDetailView(AdminRequiredMixin, DetailView):
    template_name = "admin-panel/recode_detail.html"
    model = ReCode
    context_object_name = "recode"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ReCode._meta.get_field("status").choices
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        new_status = request.POST.get("status")
        new_notes = request.POST.get("notes", "").strip()

        status_field = ReCode._meta.get_field("status")
        valid_statuses = {value for value, _ in status_field.choices}

        updated_fields = []

        # آپدیت وضعیت
        if new_status in valid_statuses and new_status != self.object.status:
            self.object.status = new_status
            updated_fields.append("status")

        # آپدیت یادداشت
        if new_notes != self.object.notes:
            self.object.notes = new_notes
            updated_fields.append("notes")

        if updated_fields:
            updated_fields.append("updated_at")
            self.object.save(update_fields=updated_fields)

        return redirect("admin_panel:recode_detail", pk=self.object.pk)
