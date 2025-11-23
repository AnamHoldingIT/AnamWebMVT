from django.db import models
from home.models import STATUS_CHOICES, STATUS_NEW


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
        ]

    def __str__(self):
        return f"{self.full_name} - {self.phone}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
