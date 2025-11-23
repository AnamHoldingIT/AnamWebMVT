from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("نام کاربری الزامی است.")

        username = username.lower().strip()
        user = self.model(username=username, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.ROLE_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("سوپریوزر باید is_staff=True باشد.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("سوپریوزر باید is_superuser=True باشد.")

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # ---- رول‌ها ----
    ROLE_ADMIN = "admin"
    ROLE_STAFF = "staff"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "مدیر سیستم"),
        (ROLE_STAFF, "کارشناس"),
    )

    # ---- اطلاعات اصلی ----
    username = models.CharField(
        "نام کاربری",
        max_length=50,
        unique=True,
        db_index=True
    )

    full_name = models.CharField(
        "نام و نام خانوادگی",
        max_length=150,
        blank=True,
        null=True
    )

    email = models.EmailField(
        "ایمیل",
        blank=True,
        null=True
    )
    phone = models.CharField(
        "شماره تماس",
        max_length=14,
        blank=True,
        null=True

    )

    role = models.CharField(
        "نقش",
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAFF,
        db_index=True
    )

    # ---- وضعیت‌ها ----
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"  # ورود با یوزرنیم
    REQUIRED_FIELDS = []  # هنگام ساخت سوپریوزر فقط پسورد می‌پرسد

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username}"
