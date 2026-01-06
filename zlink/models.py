from django.db import models
from home.models import STATUS_CHOICES, STATUS_NEW




class Referrer(models.Model):
    name = models.CharField("نام معرف", max_length=150)
    code = models.SlugField("کد معرف", max_length=50, unique=True)  # مثل anam3
    is_active = models.BooleanField("فعال", default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "معرف"
        verbose_name_plural = "معرف‌ها"

    def __str__(self):
        return f"{self.name} ({self.code})"




class ReCode(models.Model):
    first_name = models.CharField(
        'نام',
        max_length=150
    )
    last_name = models.CharField(
        'نام خانوادگی',
        max_length=150
    )
    phone = models.CharField(
        'شماره تماس',
        max_length=14,
        db_index=True,
        help_text='مثال: 09xxxxxxxxx'
    )

    email = models.EmailField(
        'ایمیل',
        max_length=254,
        null=True,
        blank=True,
        db_index=True,
        help_text='مثال: name@example.com'
    )

    # ✅ NEW
    city = models.CharField(
        'شهر',
        max_length=80,
        null=True,
        blank=True,
        db_index=True,
    )

    referrer = models.ForeignKey(
        Referrer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recode_requests",
        verbose_name="معرف"
    )

    status = models.CharField(
        'وضعیت',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True
    )

    notes = models.TextField(
        'یادداشت داخلی',
        blank=True,
        help_text='یادداشت‌های تیم آنام درباره این درخواست (برای نمایش به کاربر نیست).'
    )



    created_at = models.DateTimeField(
        'تاریخ ثبت',
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        'آخرین بروزرسانی',
        auto_now=True
    )

    class Meta:
        verbose_name = 'درخواست Recode'
        verbose_name_plural = 'درخواست‌های Recode'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email']),  # ✅ NEW
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.phone}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
