from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import *
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from .forms import LoginForm
from .models import User


class AdminLoginView(FormView):
    template_name = "accounts/admin_login.html"
    form_class = LoginForm

    # success_url را پاک کنید یا نادیده بگیرید چون تابع get_success_url جایگزین می‌شود

    def get_success_url(self):
        """
        تعیین مسیر ریدایرکت بر اساس نقش کاربر
        """
        user = self.request.user
        # اگر کاربر احراز هویت شده و نقش "ادمین بیننده" دارد -> برو به Recode
        if user.is_authenticated and getattr(user, "role", None) == User.ROLE_WATCHER_ADMIN:
            return reverse("admin_panel:recode_list")

        # در غیر این صورت (ادمین اصلی یا سوپریوزر) -> برو به داشبورد
        return reverse("admin_panel:dashboard")

    # 🔥 اگه قبلاً لاگین شده، مستقیم بفرستش به صفحه مربوطه
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and (
                user.is_superuser or
                getattr(user, "role", None) == User.ROLE_ADMIN or
                getattr(user, "role", None) == User.ROLE_WATCHER_ADMIN):
            # تغییر: استفاده از get_success_url
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(
            self.request,
            username=username,
            password=password
        )

        if user is None:
            return JsonResponse({
                "ok": False,
                "error": "نام کاربری یا رمز عبور اشتباه است."
            }, status=400)

        # دسترسی نداشتن
        if not (user.is_superuser or user.role in [User.ROLE_ADMIN, User.ROLE_WATCHER_ADMIN]):
            return JsonResponse({
                "ok": False,
                "error": "شما اجازه ورود به پنل مدیریت را ندارید."
            }, status=403)

        # لاگین
        login(self.request, user)

        # تغییر: استفاده از self.get_success_url() به جای self.success_url
        return JsonResponse({
            "ok": True,
            "redirect": self.get_success_url()
        }, status=200)

    def form_invalid(self, form):
        err_text = "لطفاً اطلاعات را صحیح وارد کنید."
        try:
            first_field = next(iter(form.errors))
            err_text = form.errors[first_field][0]
        except Exception:
            pass

        return JsonResponse({
            "ok": False,
            "error": err_text,
        }, status=400)


class AdminLogoutView(LoginRequiredMixin, View):
    login_url = reverse_lazy("home:home")  # اگر لاگین نبود → بفرست لاگین

    def get(self, request, *args, **kwargs):
        logout(request)  # خروج کاربر
        return redirect("home:home")


class UserLoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm

    def get_success_url(self):
        # اگر next بود همون، وگرنه داشبورد کاربر
        nxt = self.request.GET.get("next")
        return nxt or reverse("worklog:dashboard")

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            # اگر ادمین یا بیننده است -> بفرست به پنل ادمین (یا هر جایی که صلاح میدونی)
            if user.is_superuser or user.role in [User.ROLE_ADMIN, User.ROLE_WATCHER_ADMIN]:
                return redirect("accounts:admin_login")  # یا admin_panel:recode_list برای بیننده

            # اگر کاربر عادی است -> بفرست به success_url (داشبورد کاربر)
            return HttpResponseRedirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data["username"].strip().lower()
        password = form.cleaned_data["password"]

        user = authenticate(self.request, username=username, password=password)

        if user is None:
            messages.error(self.request, "نام کاربری یا رمز عبور صحیح نیست.")
            return self.form_invalid(form)

        if not user.is_active:
            messages.error(self.request, "حساب کاربری شما غیرفعال است.")
            return self.form_invalid(form)

        # اگر می‌خوای ادمین از این صفحه وارد نشه:
        if getattr(user, "role", None) == User.ROLE_ADMIN:
            messages.error(self.request, "لطفاً از صفحه ورود مدیران استفاده کنید.")
            return self.form_invalid(form)

        login(self.request, user)
        return redirect(self.get_success_url())
