from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from admin_panel.models import ActivityLog
from home.models import Contract
from accounts.utils.threadlocal import get_current_user


@receiver(pre_save, sender=Contract)
def contract_before_save(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی قبل از ذخیره جدید"""
    if instance.pk:
        try:
            old_obj = Contract.objects.get(pk=instance.pk)
            instance._old_status = old_obj.status
        except Contract.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Contract)
def contract_after_save(sender, instance, created, **kwargs):
    user = get_current_user()  # 🔥 دریافت کاربر واقعی
    status_display = instance.get_status_display()

    # حالت ایجاد
    if created:
        ActivityLog.objects.create(
            title=f"ثبت درخواست جدید از طرف {instance.full_name}",
            meta=f"استارتاپ: {instance.startup_name} · وضعیت: {status_display}",
            category=ActivityLog.CATEGORY_CONTRACTS,
            level=ActivityLog.LEVEL_INFO,
            actor=user,  # 🔥 ذخیره ادمین
        )
        return

    # مقایسه وضعیت جدید و قدیم
    old_status = getattr(instance, "_old_status", None)
    if old_status is None or old_status == instance.status:
        return  # تغییری نکرده

    # فارسی کردن وضعیت قبلی
    old_status_display = dict(
        Contract._meta.get_field("status").choices
    ).get(old_status, old_status)

    # تعیین سطح و عنوان
    new = instance.status.lower()

    if new == "done":
        level = ActivityLog.LEVEL_SUCCESS
        title = f"تأیید درخواست استارتاپ {instance.startup_name}"
    elif new == "in_review":
        level = ActivityLog.LEVEL_INFO
        title = f"در حال بررسی شدن درخواست {instance.startup_name}"
    else:
        level = ActivityLog.LEVEL_INFO
        title = f"تغییر وضعیت درخواست {instance.startup_name}"

    ActivityLog.objects.create(
        title=title,
        meta=f"وضعیت از «{old_status_display}» به «{status_display}» تغییر کرد.",
        category=ActivityLog.CATEGORY_CONTRACTS,
        level=level,
        actor=user,  # 🔥 ذخیره ادمین
    )


@receiver(post_delete, sender=Contract)
def contract_after_delete(sender, instance, **kwargs):
    user = get_current_user()  # 🔥 دریافت ادمین حذف‌کننده

    ActivityLog.objects.create(
        title=f"حذف درخواست مربوط به {instance.full_name}",
        meta=f"استارتاپ: {instance.startup_name}",
        category=ActivityLog.CATEGORY_CONTRACTS,
        level=ActivityLog.LEVEL_WARNING,
        actor=user,  # 🔥 ذخیره ادمین
    )
