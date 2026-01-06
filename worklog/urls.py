# worklog/urls.py
from django.urls import path
from .views import (UserDashboardView, UserProjectsView, UserPlanListView, PlanWizardCreateView, PlanEditView,
                    UserReportListView, UserReportView ,PlanDeleteView , UserReportDetailView)

app_name = "worklog"

urlpatterns = [
    path("", UserDashboardView.as_view(), name="dashboard"),
    path("projects/", UserProjectsView.as_view(), name="projects"),
    path("plans/", UserPlanListView.as_view(), name="plans"),
    path("plans/new/<int:member_id>/", PlanWizardCreateView.as_view(), name="plan_wizard"),
    path("plans/<int:plan_id>/edit/", PlanEditView.as_view(), name="plan_edit"),
    path("reports/", UserReportListView.as_view(), name="report_list"),
    path("reports/<int:plan_id>/", UserReportView.as_view(), name="report"),  # ✅ ثبت/مشاهده گزارش همان روز
    path("reports/<int:plan_id>/view/", UserReportDetailView.as_view(), name="report_view"),

    path("plans/<int:plan_id>/delete/", PlanDeleteView.as_view(), name="plan_delete"),

]
