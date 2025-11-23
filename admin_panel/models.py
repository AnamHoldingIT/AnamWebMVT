from django.db import models

import accounts.models
from accounts.models import User
from django.utils import timezone

# Create your models here.
class ActivityLog(models.Model):
    CATEGORY_CONTRACTS = "contracts"
    CATEGORY_USERS = "users"
    CATEGORY_SECURITY = "security"
    CATEGORY_SETTINGS = "settings"

    CATEGORY_CHOICES = (
        (CATEGORY_CONTRACTS, "درخواست‌ها"),
        (CATEGORY_USERS, "کاربران"),
        (CATEGORY_SECURITY, "امنیت"),
        (CATEGORY_SETTINGS, "تنظیمات"),
    )

    LEVEL_SUCCESS = "success"
    LEVEL_INFO = "info"
    LEVEL_WARNING = "warning"
    LEVEL_NEUTRAL = "neutral"

    LEVEL_CHOICES = (
        (LEVEL_SUCCESS, "موفق"),
        (LEVEL_INFO, "اطلاع"),
        (LEVEL_WARNING, "هشدار"),
        (LEVEL_NEUTRAL, "عادی"),
    )

    title = models.CharField("عنوان", max_length=200)
    meta = models.CharField("توضیح کوتاه", max_length=250, blank=True)
    category = models.CharField("دسته", max_length=20, choices=CATEGORY_CHOICES)
    level = models.CharField(
        "نوع",
        max_length=20,
        choices=LEVEL_CHOICES,
        default=LEVEL_INFO,
    )
    actor = models.ForeignKey(
        User,
        verbose_name="کاربر انجام‌دهنده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("زمان ثبت", default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "فعالیت"
        verbose_name_plural = "فعالیت‌ها"

    def __str__(self):
        return self.title
