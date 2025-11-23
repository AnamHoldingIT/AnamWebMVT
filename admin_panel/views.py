# admin_panel/views.py
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from .forms import *
from accounts.models import User
from home.models import Contract
from .models import ActivityLog
from home.models import SiteStat
from django.db.models import Q
from zlink.models import ReCode


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.is_superuser or getattr(user, "role", None) == User.ROLE_ADMIN


class DashboardView(AdminRequiredMixin, TemplateView):
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


class ContractListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/contracts_list.html"
    model = Contract
    context_object_name = "contracts"
    paginate_by = 20


class ContractDetailView(AdminRequiredMixin, DetailView):
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


class UserListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/user_list.html"
    model = User
    context_object_name = "users"
    paginate_by = 10


class UserDetailView(AdminRequiredMixin, UpdateView):
    model = User
    template_name = "admin-panel/user_detail.html"
    form_class = UserEditForm
    context_object_name = "user_obj"

    def get_success_url(self):
        return reverse_lazy("admin_panel:user_detail", kwargs={"pk": self.object.pk})


class UserCreateView(AdminRequiredMixin, CreateView):
    template_name = "admin-panel/user_create.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("admin_panel:users")


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = "admin-panel/user_delete_confirm.html"
    success_url = reverse_lazy("admin_panel:users")



class UserResetPasswordView(AdminRequiredMixin, FormView):
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
        qs = super().get_queryset()

        # فیلتر وضعیت
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # جستجو روی نام / نام خانوادگی / شماره
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(phone__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        status_field = ReCode._meta.get_field("status")
        ctx["status_choices"] = status_field.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["query"] = self.request.GET.get("q", "")
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
