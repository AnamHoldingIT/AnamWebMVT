import re
from django import forms
from django.core.exceptions import ValidationError
from .models import ReCode


class ReCodeForm(forms.ModelForm):
    class Meta:
        model = ReCode
        fields = ["first_name", "last_name", "phone", "email", "city"]  # ✅ NEW

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()

        if not re.match(r"^09\d{9}$", phone):
            raise ValidationError("شماره تماس معتبر وارد کنید (مثال: 09xxxxxxxxx).")

        if ReCode.objects.filter(phone=phone).exists():
            raise ValidationError("این شماره قبلاً ثبت شده است. منتظر تماس تیم آنام باشید.")

        return phone

    # ✅ NEW
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        # EmailField خودش format رو چک می‌کنه؛ اینجا فقط تکراری رو می‌گیریم
        if ReCode.objects.filter(email__iexact=email).exists():
            raise ValidationError("این ایمیل قبلاً ثبت شده است. منتظر تماس تیم آنام باشید.")

        return email

    # ✅ NEW
    def clean_city(self):
        city = (self.cleaned_data.get("city") or "").strip()

        if len(city) < 2:
            raise ValidationError("نام شهر را درست وارد کنید.")

        # اجازه حروف فارسی/انگلیسی + فاصله و نیم‌فاصله و -
        if not re.match(r"^[\u0600-\u06FFa-zA-Z\s‌\-]{2,80}$", city):
            raise ValidationError("نام شهر معتبر نیست.")

        return city
