import re
from django import forms
from django.core.exceptions import ValidationError
from .models import ReCode


class ReCodeForm(forms.ModelForm):
    class Meta:
        model = ReCode
        fields = ["first_name", "last_name", "phone"]

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()

        # ولیدیشن ساده موبایل
        if not re.match(r"^09\d{9}$", phone):
            raise ValidationError("شماره تماس معتبر وارد کنید (مثال: 09xxxxxxxxx).")

        # جلوگیری از ثبت تکراری
        if ReCode.objects.filter(phone=phone).exists():
            raise ValidationError("این شماره قبلاً ثبت شده است. منتظر تماس تیم آنام باشید.")

        return phone
