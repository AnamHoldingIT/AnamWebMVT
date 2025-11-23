from django.db import models
from django.core.validators import RegexValidator
from .status import *


class Contract(models.Model):
    full_name = models.CharField(
        'نام و نام خانوادگی',
        max_length=150
    )

    phone = models.CharField(
        'شماره تماس',
        max_length=14,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{8,14}$',
                message='شماره تماس معتبر وارد کنید.'
            )
        ],
        db_index=True,  # برای سرچ سریع در ادمین
    )

    startup_name = models.CharField(
        'نام استارتاپ / ایده',
        max_length=200
    )

    email = models.EmailField(
        'ایمیل',
        blank=True,
        null=True
    )

    detail = models.TextField(
        'توضیحات کوتاه درباره محصول',
    )

    status = models.CharField(
        'وضعیت',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True
    )

    is_read = models.BooleanField(
        'خوانده شده؟',
        default=False,
        db_index=True
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
        ordering = ['-created_at']
        verbose_name = 'درخواست شتاب‌دهی / قرارداد'
        verbose_name_plural = 'درخواست‌های شتاب‌دهی / قرارداد'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['status', 'is_read']),
        ]

    def __str__(self):
        return f'{self.full_name} – {self.phone}'


class SiteStat(models.Model):
    total_views = models.PositiveBigIntegerField(
        "تعداد بازدید سایت",
        default=0,
    )

    updated_at = models.DateTimeField(
        "آخرین بروزرسانی",
        auto_now=True,
    )

    class Meta:
        verbose_name = "آمار سایت"
        verbose_name_plural = "آمار سایت"

    def __str__(self):
        return f"آمار سایت (بازدیدها: {self.total_views})"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def increase_views(cls, step=1):
        obj = cls.get_solo()
        obj.total_views = (obj.total_views or 0) + step
        obj.save(update_fields=["total_views", "updated_at"])
        return obj.total_views
