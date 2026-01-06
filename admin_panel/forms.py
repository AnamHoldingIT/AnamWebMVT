# admin_panel/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.forms import formset_factory

from worklog.models import Project, ProjectMember

User = get_user_model()


# ----------------------------
# Users
# ----------------------------
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "role", "is_active"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
        label="رمز عبور",
    )

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "phone", "role", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
        label="رمز عبور جدید",
    )


# ----------------------------
# Project Create (Base)
# ----------------------------
class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "sheet_url", "is_active"]

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise forms.ValidationError("عنوان پروژه الزامی است.")
        return title

    def clean_sheet_url(self):
        url = (self.cleaned_data.get("sheet_url") or "").strip()
        if not url:
            raise forms.ValidationError("لینک گوگل شیت الزامی است.")
        return url


# ----------------------------
# Project Members Formset Row
# ----------------------------
class ProjectMemberCreateForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="انتخاب کاربر...",
        label="کاربر",
    )
    role = forms.ChoiceField(
        choices=ProjectMember.ROLE_CHOICES,
        required=False,
        label="نقش",
    )
    DELETE = forms.BooleanField(required=False)

    def __init__(self, *args, users_qs=None, **kwargs):
        super().__init__(*args, **kwargs)

        if users_qs is None:
            users_qs = (
                User.objects.filter(is_active=True)
                .only("id", "username", "full_name")
                .order_by("-date_joined")
            )

        # ✅ حیاتی: queryset همینجا ست می‌شود
        self.fields["user"].queryset = users_qs

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("DELETE"):
            return cleaned

        user = cleaned.get("user")
        role = cleaned.get("role")

        # ✅ ردیف کاملاً خالی مشکلی ندارد (JS ممکنه فرم خالی بسازه)
        if not user and not role:
            return cleaned

        # اگر user انتخاب شده ولی role خالیه → پیش‌فرض عضو
        if user and not role:
            cleaned["role"] = ProjectMember.ROLE_MEMBER
            return cleaned

        # اگر role هست ولی user نیست → خطا
        if role and not user:
            raise forms.ValidationError("کاربر انتخاب نشده است.")

        # role باید معتبر باشد
        valid_roles = {c[0] for c in ProjectMember.ROLE_CHOICES}
        if role and role not in valid_roles:
            raise forms.ValidationError("نقش نامعتبر است.")

        return cleaned


ProjectMemberFormSet = formset_factory(
    ProjectMemberCreateForm,
    extra=0,        # ردیف‌ها با JS اضافه می‌شن
    can_delete=True
)
