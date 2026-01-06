from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


# ==========================
#  CHOICES حرفه‌ای
# ==========================

class ProjectCategory(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(unique=True, allow_unicode=True)
    icon_class = models.CharField(
        "کلاس آیکن بوت‌استرپ",
        max_length=50,
        blank=True,
        help_text='مثلاً: "bi-credit-card" یا "bi-cpu"'
    )

    class Meta:
        ordering = ['name']
        verbose_name = "دسته‌بندی پروژه"
        verbose_name_plural = "دسته‌بندی پروژه‌ها"

    def __str__(self):
        return self.name


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "فعال"
    PAUSED = "paused", "موقتا متوقف"
    EXITED = "exited", "خروج"
    INTERNAL = "internal", "پروژه داخلی"


class CollaborationModel(models.TextChoices):
    INVESTMENT = "investment", "سرمایه‌گذاری"
    ACCELERATION = "acceleration", "شتاب‌دهی"
    BOTH = "both", "سرمایه‌گذاری + شتاب‌دهی"
    CONSULTING = "consulting", "مشاوره و همراهی مدیریتی"


# ==========================
#  MANAGER برای فقط پروژه‌های فعال
# ==========================

class ActiveProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=ProjectStatus.ACTIVE
        )


# ==========================
#  MODEL اصلی: PortfolioProject
# ==========================

class PortfolioProject(models.Model):
    # نام‌ها
    name_fa = models.CharField(
        "نام پروژه (فارسی)",
        max_length=150,
        db_index=True,
    )
    name_en = models.CharField(
        "نام پروژه (انگلیسی)",
        max_length=150,
        blank=True,
        null=True,
        help_text="برای استفاده در داشبورد، سئو یا برندینگ بین‌المللی.",
    )

    slug = models.SlugField(
        "اسلاگ (آدرس یکتا)",
        max_length=160,
        unique=True,
        allow_unicode=True,
        help_text="برای URL صفحه جزئیات، مثلا: novapay",
    )

    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="projects",
    )

    status = models.CharField(
        "وضعیت پروژه در پورتفوی",
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
        db_index=True,
    )

    collaboration_model = models.CharField(
        "مدل همکاری با آنام",
        max_length=20,
        choices=CollaborationModel.choices,
        default=CollaborationModel.BOTH,
    )

    # متن‌های کوتاه برای کارت‌ها و هدر
    short_tagline = models.CharField(
        "توضیح کوتاه (کارت / لیست)",
        max_length=230,
        help_text="همون جمله کوتاهی که روی کارت و لیست نمایش داده می‌شه.",
    )

    hero_subtitle = models.CharField(
        "زیرتیتر در صفحه جزئیات",
        max_length=300,
        help_text="یک جمله کمی توضیحی‌تر که زیر عنوان در صفحه جزئیات می‌آید.",
    )

    list_summary = models.TextField(
        "خلاصه برای صفحه لیست",
        blank=True,
        help_text="در صورت نیاز، توضیح کمی بلندتر برای صفحه لیست. می‌تونه خالی بمونه.",
    )

    detail_summary = models.TextField(
        "خلاصه اصلی در صفحه جزئیات",
        blank=True,
        help_text="متن اصلی «چکیده پروژه»؛ می‌تونی همون چیزی که الان تو NovaPay نوشتی اینجا بذاری.",
    )

    # انتخاب برای نمایش در صفحه اصلی و ترتیب‌ها
    is_featured_home = models.BooleanField(
        "نمایش در صفحه اصلی؟",
        default=False,
        db_index=True,
    )

    home_order = models.PositiveSmallIntegerField(
        "ترتیب نمایش در صفحه اصلی",
        default=0,
        help_text="هرچه عدد کمتر، بالاتر نشان داده می‌شود.",
    )

    list_order = models.PositiveSmallIntegerField(
        "ترتیب نمایش در صفحه لیست",
        default=0,
        help_text="ترتیب پیش‌فرض در صفحه پورتفوی.",
    )

    # تصاویر
    image = models.ImageField(
        "تصویر",
        upload_to="portfolio/",
        help_text="برای کارت صفحه اصلی و صفحه لیست.",
    )

    # زمان‌ها
    created_at = models.DateTimeField(
        "تاریخ ثبت در پورتفوی",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "آخرین بروزرسانی",
        auto_now=True,
    )

    objects = models.Manager()
    active = ActiveProjectManager()

    class Meta:
        ordering = ["-is_featured_home", "home_order", "list_order", "-created_at"]
        verbose_name = "پروژه پورتفوی"
        verbose_name_plural = "پروژه‌های پورتفوی"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status", "is_featured_home"]),
        ]

    def __str__(self):
        return self.name_fa

    def get_absolute_url(self):
        """
        آدرس صفحه جزئیات پروژه، مثلا:
        /portfolio/novapay/
        """
        return reverse("portfolio:portfolio_details", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        """
        اگر اسلاگ خالی بود، به صورت خودکار از روی name_en
        و در صورت نبودن، از name_fa ساخته می‌شود.
        """
        if not self.slug:
            base = self.name_en or self.name_fa
            if base:
                self.slug = slugify(base, allow_unicode=True)
        super().save(*args, **kwargs)


# ==========================
#  نقش آنام در پروژه (چِیپ‌ها)
# ==========================

class ProjectRole(models.Model):
    title = models.CharField(
        "عنوان نقش",
        max_length=120,
        help_text="مثلا: طراحی مسیر رشد، ساختاردهی تیم، سرمایه‌گذاری و همراهی مدیریتی",
    )
    slug = models.SlugField(
        "اسلاگ",
        max_length=120,
        unique=True,
        allow_unicode=True,
        help_text="کوتاه و یکتا برای استفاده احتمالی در فیلتر یا API.",
    )

    class Meta:
        verbose_name = "نقش آنام در پروژه"
        verbose_name_plural = "نقش‌های آنام در پروژه‌ها"
        ordering = ["title"]

    def __str__(self):
        return self.title


class ProjectRoleAssignment(models.Model):
    """
    جدول میانی M2M با امکان ترتیب نمایش نقش‌ها برای هر پروژه.
    """
    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="role_assignments",
        verbose_name="پروژه",
    )
    role = models.ForeignKey(
        ProjectRole,
        on_delete=models.CASCADE,
        related_name="project_assignments",
        verbose_name="نقش",
    )
    order = models.PositiveSmallIntegerField(
        "ترتیب نمایش",
        default=0,
    )

    class Meta:
        verbose_name = "نقش اختصاص‌داده‌شده به پروژه"
        verbose_name_plural = "نقش‌های اختصاص‌داده‌شده به پروژه‌ها"
        ordering = ["order"]
        unique_together = ("project", "role")

    def __str__(self):
        return f"{self.project} – {self.role}"


# برای راحتی دسترسی: project.roles.all() در تمپلیت
PortfolioProject.add_to_class(
    "roles",
    property(lambda self: [ra.role for ra in self.role_assignments.all()])
)


# ==========================
#  هایلایت‌ها (همون سه چیپ طلایی پایین کارت چکیده)
# ==========================

class ProjectHighlight(models.Model):
    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="highlights",
        verbose_name="پروژه",
    )

    text = models.CharField(
        "متن هایلایت",
        max_length=180,
        help_text="مثلا: تمرکز روی B2B و Enterprise",
    )

    icon_class = models.CharField(
        "کلاس آیکن (Bootstrap Icon)",
        max_length=50,
        blank=True,
        help_text='مثلا: "bi-graph-up-arrow" یا "bi-shield-lock" (اختیاری)',
    )

    order = models.PositiveSmallIntegerField(
        "ترتیب نمایش",
        default=0,
    )

    class Meta:
        verbose_name = "هایلایت پروژه"
        verbose_name_plural = "هایلایت‌های پروژه"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.project} – {self.text[:40]}..."


# ==========================
#  متریک‌ها (اعداد بخش «تصویر کلی نتایج»)
# ==========================

class ProjectMetric(models.Model):
    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="metrics",
        verbose_name="پروژه",
    )

    label = models.CharField(
        "عنوان متریک",
        max_length=150,
        help_text="مثلا: رشد متوسط ماهانه GMV",
    )

    value = models.CharField(
        "مقدار متریک",
        max_length=50,
        help_text='مثلا: "+۱۸٪" یا "۳.۱x"',
    )

    order = models.PositiveSmallIntegerField(
        "ترتیب نمایش",
        default=0,
    )

    class Meta:
        verbose_name = "متریک پروژه"
        verbose_name_plural = "متریک‌های پروژه"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.project} – {self.label}"


# ==========================
#  مراحل مسیر همکاری (timeline سه‌مرحله‌ای)
# ==========================

class ProjectJourneyStep(models.Model):
    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="journey_steps",
        verbose_name="پروژه",
    )

    step_number = models.PositiveSmallIntegerField(
        "شماره مرحله",
        help_text="مثلا: ۱، ۲، ۳ – برای نمایش در دایره طلایی.",
    )

    title = models.CharField(
        "عنوان مرحله",
        max_length=150,
        help_text="مثلا: تشخیص گلوگاه‌های کلیدی",
    )

    description = models.TextField(
        "توضیح مرحله",
        help_text="توضیح کوتاه برای هر مرحله، مشابه چیزی که الان در صفحه NovaPay نوشتی.",
    )

    class Meta:
        verbose_name = "مرحله مسیر همکاری"
        verbose_name_plural = "مراحل مسیر همکاری پروژه"
        ordering = ["step_number"]
        unique_together = ("project", "step_number")

    def __str__(self):
        return f"{self.project} – مرحله {self.step_number}"
