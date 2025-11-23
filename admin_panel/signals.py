# admin_panel/signals.py

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from accounts.models import User
from .models import ActivityLog
from accounts.utils.threadlocal import get_current_user

# فیلدهایی که می‌خوای روی تغییرشون لاگ ثبت بشه
TRACKED_USER_FIELDS = ["full_name", "email", "phone", "role", "is_active", "is_staff", "is_superuser"]


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """
    قبل از ذخیره، نسخه قبلی کاربر رو نگه می‌داریم تا بفهمیم چه فیلدهایی عوض شده.
    """
    if not instance.pk:
        instance._old_state = None
        return

    try:
        old_obj = sender.objects.get(pk=instance.pk)
        instance._old_state = old_obj
    except sender.DoesNotExist:
        instance._old_state = None


@receiver(post_save, sender=User)
def log_user_save(sender, instance, created, **kwargs):
    """
    لاگ ساخت یا ویرایش کاربر
    """
    actor = get_current_user()  # 🔥 ادمینی که الان این تغییر رو زده (اگه از طریق request بوده)

    # -------------------------
    #  حالت ایجاد
    # -------------------------
    if created:
        ActivityLog.objects.create(
            title=f"ایجاد کاربر جدید: {instance.username}",
            meta=f"نقش: {instance.get_role_display()}",
            category=ActivityLog.CATEGORY_USERS,
            level=ActivityLog.LEVEL_SUCCESS,
            actor=actor,
        )
        return

    # -------------------------
    #  حالت ویرایش
    # -------------------------
    old = getattr(instance, "_old_state", None)
    if not old:
        return

    changed_fields = []
    changes_detail = []

    for field in TRACKED_USER_FIELDS:
        old_val = getattr(old, field, None)
        new_val = getattr(instance, field, None)

        if old_val == new_val:
            continue

        # نمایش قشنگ‌تر برای بعضی فیلدها
        if field == "role":
            old_val_disp = old.get_role_display()
            new_val_disp = instance.get_role_display()
            label = "نقش"
        elif field == "is_active":
            old_val_disp = "فعال" if old_val else "غیرفعال"
            new_val_disp = "فعال" if new_val else "غیرفعال"
            label = "وضعیت فعال بودن"
        elif field == "is_staff":
            old_val_disp = "دسترسی ادمین دارد" if old_val else "کاربر عادی"
            new_val_disp = "دسترسی ادمین دارد" if new_val else "کاربر عادی"
            label = "سطح دسترسی (is_staff)"
        elif field == "is_superuser":
            old_val_disp = "سوپریوزر" if old_val else "غیر سوپریوزر"
            new_val_disp = "سوپریوزر" if new_val else "غیر سوپریوزر"
            label = "سوپریوزر"
        else:
            old_val_disp = old_val
            new_val_disp = new_val
            label = field

        changed_fields.append(field)
        changes_detail.append(f"{label}: «{old_val_disp}» → «{new_val_disp}»")

    if not changed_fields:
        return  # هیچ فیلد مهمی تغییر نکرده

    changes_str = " | ".join(changes_detail)

    ActivityLog.objects.create(
        title=f"ویرایش مشخصات کاربر: {instance.username}",
        meta=f"تغییرات: {changes_str}",
        category=ActivityLog.CATEGORY_USERS,
        level=ActivityLog.LEVEL_INFO,
        actor=actor,
    )


@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    """
    حذف کاربر
    """
    actor = get_current_user()  # کسی که حذف کرده

    ActivityLog.objects.create(
        title=f"حذف کاربر: {instance.username}",
        meta=f"کاربر با نقش {instance.get_role_display()} حذف شد.",
        category=ActivityLog.CATEGORY_USERS,
        level=ActivityLog.LEVEL_WARNING,
        actor=actor,
    )
