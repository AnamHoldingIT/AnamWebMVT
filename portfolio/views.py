from django.shortcuts import render
from django.views.generic import *

from portfolio.models import PortfolioProject, ProjectCategory, ProjectStatus


# Create your views here.




class PortfolioListView(ListView):
    """
    صفحه لیست پورتفوی
    /portfolio/
    """
    model = PortfolioProject
    template_name = "portfolio/portfolio-list.html"
    context_object_name = "projects"

    def get_queryset(self):
        # فقط پروژه‌های فعال + بهینه‌سازی کوئری‌ها
        return (
            PortfolioProject.active
            .select_related("category")
            .prefetch_related(
                "highlights",
                "metrics",
                "journey_steps",
                "role_assignments__role",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # دسته‌بندی‌هایی که حداقل یک پروژه فعال دارند
        categories = (
            ProjectCategory.objects
            .filter(projects__status=ProjectStatus.ACTIVE)
            .distinct()
            .order_by("name")
        )

        context["categories"] = categories
        context["active_count"] = PortfolioProject.active.count()
        return context


class PortfolioDetailView(DetailView):
    """
    صفحه جزئیات هر پروژه
    /portfolio/<slug>/
    """
    model = PortfolioProject
    template_name = "portfolio/portfolio-details.html"
    context_object_name = "project"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        # برای جزئیات هم همون prefetch ها
        return (
            PortfolioProject.objects
            .select_related("category")
            .prefetch_related(
                "highlights",
                "metrics",
                "journey_steps",
                "role_assignments__role",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        # اینا رو برای راحتی تو تمپلیت می‌فرستیم
        context["highlights"] = project.highlights.all()
        context["metrics"] = project.metrics.all()
        context["journey_steps"] = project.journey_steps.all()
        context["roles"] = project.roles  # همون property که تو مدل اضافه کردیم

        return context