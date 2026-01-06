from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import ReCode
from admin_panel.models import ActivityLog
from accounts.utils.threadlocal import get_current_user


# ✅ NEW: email و city اضافه شد
TRACKED_FIELDS = ["first_name", "last_name", "phone", "email", "city", "status", "notes"]


@receiver(pre_save, sender=ReCode)
def recode_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_state = None
        return

    try:
        old_obj = sender.objects.get(pk=instance.pk)
        instance._old_state = old_obj
    except sender.DoesNotExist:
        instance._old_state = None


@receiver(post_save, sender=ReCode)
def recode_post_save(sender, instance, created, **kwargs):
    user = get_current_user()

    if created:
        ActivityLog.objects.create(
            title="ثبت درخواست جدید Recode",
            meta=f"{instance.full_name} · شماره تماس: {instance.phone}",
            category=ActivityLog.CATEGORY_CONTRACTS,
            level=ActivityLog.LEVEL_SUCCESS,
            actor=user,
        )
        return

    old = getattr(instance, "_old_state", None)
    if not old:
        return

    changed_fields = []
    changes_detail = []

    for field in TRACKED_FIELDS:
        old_val = getattr(old, field, None)
        new_val = getattr(instance, field, None)

        if old_val != new_val:
            changed_fields.append(field)
            changes_detail.append(f"{field}: «{old_val}» → «{new_val}»")

    if not changed_fields:
        return

    changes_str = " | ".join(changes_detail)

    ActivityLog.objects.create(
        title="ویرایش درخواست Recode",
        meta=f"{instance.full_name} – تغییرات: {changes_str}",
        category=ActivityLog.CATEGORY_CONTRACTS,
        level=ActivityLog.LEVEL_INFO,
        actor=user,
    )


@receiver(post_delete, sender=ReCode)
def recode_post_delete(sender, instance, **kwargs):
    user = get_current_user()

    ActivityLog.objects.create(
        title="حذف درخواست Recode",
        meta=f"{instance.full_name} · {instance.phone}",
        category=ActivityLog.CATEGORY_CONTRACTS,
        level=ActivityLog.LEVEL_WARNING,
        actor=user,
    )
