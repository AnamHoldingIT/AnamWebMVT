from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import *
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from .forms import LoginForm
from .models import User


class AdminLoginView(FormView):
    template_name = "accounts/admin_login.html"
    form_class = LoginForm
    success_url = reverse_lazy("admin_panel:dashboard")

    # 🔥 اگه قبلاً لاگین شده و ادمینه، مستقیم بفرستش داشبورد
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and (user.is_superuser or getattr(user, "role", None) == User.ROLE_ADMIN):
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

        # یوزرنیم یا پسورد اشتباه
        if user is None:
            return JsonResponse({
                "ok": False,
                "error": "نام کاربری یا رمز عبور اشتباه است."
            }, status=400)

        # دسترسی نداشتن
        if not (user.is_superuser or user.role == User.ROLE_ADMIN):
            return JsonResponse({
                "ok": False,
                "error": "شما اجازه ورود به پنل مدیریت را ندارید."
            }, status=403)

        # لاگین
        login(self.request, user)

        return JsonResponse({
            "ok": True,
            "redirect": str(self.success_url)
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
    login_url = reverse_lazy("accounts:admin_login")  # اگر لاگین نبود → بفرست لاگین

    def get(self, request, *args, **kwargs):
        logout(request)  # خروج کاربر
        return redirect("accounts:admin_login")


class UserLoginView(TemplateView):
    template_name = 'accounts/login.html'
