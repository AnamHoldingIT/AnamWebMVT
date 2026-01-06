# admin_panel/views_portfolio.py
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import Http404
from django.db.models import Q, Count
from django.forms import modelform_factory

from .mixins import AdminRequiredMixin  # پیشنهاد: میکسین رو منتقل کن به mixins.py
from portfolio.models import (
    PortfolioProject,
    ProjectCategory,
    ProjectRole,
    ProjectRoleAssignment,
    ProjectHighlight,
    ProjectMetric,
    ProjectJourneyStep,
)

# ======================================================
# Projects CRUD
# ======================================================

ProjectForm = modelform_factory(
    PortfolioProject,
    fields=[
        "name_fa", "name_en", "slug",
        "category", "status", "collaboration_model",
        "short_tagline", "hero_subtitle",
        "list_summary", "detail_summary",
        "is_featured_home", "home_order", "list_order",
        "image",
    ]
)


class AdminPortfolioProjectListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/portfolio/project_list_admin.html"
    model = PortfolioProject
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            PortfolioProject.objects
            .select_related("category")
            .annotate(
                highlights_count=Count("highlights", distinct=True),
                metrics_count=Count("metrics", distinct=True),
                steps_count=Count("journey_steps", distinct=True),
                roles_count=Count("role_assignments", distinct=True),
            )
            .order_by("-is_featured_home", "home_order", "list_order", "-created_at")
        )

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name_fa__icontains=q) |
                Q(name_en__icontains=q) |
                Q(slug__icontains=q) |
                Q(short_tagline__icontains=q)
            )

        status = self.request.GET.get("status", "").strip()
        if status:
            qs = qs.filter(status=status)

        cat = self.request.GET.get("category", "").strip()
        if cat:
            qs = qs.filter(category_id=cat)

        featured = self.request.GET.get("featured", "").strip()
        if featured in {"0", "1"}:
            qs = qs.filter(is_featured_home=(featured == "1"))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = PortfolioProject._meta.get_field("status").choices
        ctx["categories"] = ProjectCategory.objects.all().order_by("name")

        ctx["q"] = self.request.GET.get("q", "")
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_category"] = self.request.GET.get("category", "")
        ctx["current_featured"] = self.request.GET.get("featured", "")
        return ctx


class AdminPortfolioProjectDetailView(AdminRequiredMixin, DetailView):
    template_name = "admin-panel/portfolio/project_detail_admin.html"
    model = PortfolioProject
    context_object_name = "project"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
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
        ctx = super().get_context_data(**kwargs)
        p = self.object
        ctx["highlights"] = p.highlights.all()
        ctx["metrics"] = p.metrics.all()
        ctx["journey_steps"] = p.journey_steps.all().order_by("step_number")
        ctx["role_assignments"] = p.role_assignments.select_related("role").order_by("order")

        # برای فرم assign role
        ctx["all_roles"] = ProjectRole.objects.all().order_by("title")
        ctx["categories"] = ProjectCategory.objects.all().order_by("name")
        return ctx


class AdminPortfolioProjectCreateView(AdminRequiredMixin, CreateView):
    template_name = "admin-panel/portfolio/project_form_admin.html"
    form_class = ProjectForm
    success_url = reverse_lazy("admin_panel:portfolio_projects")


class AdminPortfolioProjectUpdateView(AdminRequiredMixin, UpdateView):
    template_name = "admin-panel/portfolio/project_form_admin.html"
    model = PortfolioProject
    form_class = ProjectForm
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_success_url(self):
        return reverse_lazy("admin_panel:portfolio_project_detail", kwargs={"slug": self.object.slug})


class AdminPortfolioProjectDeleteView(AdminRequiredMixin, DeleteView):
    template_name = "admin-panel/portfolio/project_confirm_delete_admin.html"
    model = PortfolioProject
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("admin_panel:portfolio_projects")


# ======================================================
# Categories CRUD
# ======================================================

CategoryForm = modelform_factory(ProjectCategory, fields=["name", "slug", "icon_class"])


class AdminProjectCategoryListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/portfolio/category_list_admin.html"
    model = ProjectCategory
    context_object_name = "categories"
    ordering = ["name"]


class AdminProjectCategoryCreateView(AdminRequiredMixin, CreateView):
    template_name = "admin-panel/portfolio/category_form_admin.html"
    form_class = CategoryForm
    success_url = reverse_lazy("admin_panel:portfolio_categories")


class AdminProjectCategoryUpdateView(AdminRequiredMixin, UpdateView):
    template_name = "admin-panel/portfolio/category_form_admin.html"
    form_class = CategoryForm
    model = ProjectCategory
    success_url = reverse_lazy("admin_panel:portfolio_categories")


class AdminProjectCategoryDeleteView(AdminRequiredMixin, DeleteView):
    template_name = "admin-panel/portfolio/category_confirm_delete_admin.html"
    model = ProjectCategory
    success_url = reverse_lazy("admin_panel:portfolio_categories")


# ======================================================
# Roles CRUD (پیشنهادی برای مدیریت نقش‌ها)
# ======================================================

RoleForm = modelform_factory(ProjectRole, fields=["title", "slug"])


class AdminProjectRoleListView(AdminRequiredMixin, ListView):
    template_name = "admin-panel/portfolio/role_list_admin.html"
    model = ProjectRole
    context_object_name = "roles"
    ordering = ["title"]


class AdminProjectRoleCreateView(AdminRequiredMixin, CreateView):
    template_name = "admin-panel/portfolio/role_form_admin.html"
    form_class = RoleForm
    success_url = reverse_lazy("admin_panel:portfolio_roles")


class AdminProjectRoleUpdateView(AdminRequiredMixin, UpdateView):
    template_name = "admin-panel/portfolio/role_form_admin.html"
    form_class = RoleForm
    model = ProjectRole
    success_url = reverse_lazy("admin_panel:portfolio_roles")


class AdminProjectRoleDeleteView(AdminRequiredMixin, DeleteView):
    template_name = "admin-panel/portfolio/role_confirm_delete_admin.html"
    model = ProjectRole
    success_url = reverse_lazy("admin_panel:portfolio_roles")


# ======================================================
# Child Items CRUD (GENERIC: highlight / metric / step / role-assign)
# ======================================================

CHILD_CONFIG = {
    "highlight": {
        "model": ProjectHighlight,
        "fields": ["text", "icon_class", "order"],
        "title": "هایلایت",
        "needs_project": True,
    },
    "metric": {
        "model": ProjectMetric,
        "fields": ["label", "value", "order"],
        "title": "متریک",
        "needs_project": True,
    },
    "step": {
        "model": ProjectJourneyStep,
        "fields": ["step_number", "title", "description"],
        "title": "مرحله مسیر",
        "needs_project": True,
    },
    "role_assign": {
        "model": ProjectRoleAssignment,
        "fields": ["role", "order"],
        "title": "نقش پروژه",
        "needs_project": True,
    },
}


def get_child_conf(item_type: str):
    conf = CHILD_CONFIG.get(item_type)
    if not conf:
        raise Http404("Invalid item type")
    return conf


class AdminProjectChildCreateView(AdminRequiredMixin, CreateView):
    template_name = "admin-panel/portfolio/item_form_admin.html"

    def dispatch(self, request, *args, **kwargs):
        self.item_type = kwargs["item_type"]
        self.conf = get_child_conf(self.item_type)
        self.model = self.conf["model"]
        self.project = get_object_or_404(PortfolioProject, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return modelform_factory(self.model, fields=self.conf["fields"])

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.item_type == "role_assign":
            used = self.project.role_assignments.values_list("role_id", flat=True)
            form.fields["role"].queryset = ProjectRole.objects.exclude(id__in=used).order_by("title")

        return form

    def form_valid(self, form):
        form.instance.project = self.project  # ✅ فقط همین
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("admin_panel:portfolio_project_detail", kwargs={"slug": self.project.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        ctx["item_type"] = self.item_type
        ctx["item_title"] = self.conf["title"]
        ctx["mode"] = "create"
        return ctx


class AdminProjectChildUpdateView(AdminRequiredMixin, UpdateView):
    template_name = "admin-panel/portfolio/item_form_admin.html"

    def dispatch(self, request, *args, **kwargs):
        self.item_type = kwargs["item_type"]
        self.conf = get_child_conf(self.item_type)
        self.model = self.conf["model"]
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related("project")

    def get_form_class(self):
        return modelform_factory(self.model, fields=self.conf["fields"])

    def get_success_url(self):
        return reverse_lazy("admin_panel:portfolio_project_detail", kwargs={"slug": self.object.project.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        ctx["item_type"] = self.item_type
        ctx["item_title"] = self.conf["title"]
        ctx["mode"] = "edit"
        return ctx


class AdminProjectChildDeleteView(AdminRequiredMixin, DeleteView):
    template_name = "admin-panel/portfolio/item_confirm_delete_admin.html"

    def dispatch(self, request, *args, **kwargs):
        self.item_type = kwargs["item_type"]
        self.conf = get_child_conf(self.item_type)
        self.model = self.conf["model"]
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.select_related("project")

    def get_success_url(self):
        return reverse_lazy("admin_panel:portfolio_project_detail", kwargs={"slug": self.object.project.slug})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.object.project
        ctx["item_type"] = self.item_type
        ctx["item_title"] = self.conf["title"]
        return ctx
