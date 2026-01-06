from django.urls import path
from . import views
from .views_portfolio import *
from .views_worklog import *

app_name = 'admin_panel'

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("contracts/", views.ContractListView.as_view(), name="contracts"),
    path("contracts/<int:pk>/", views.ContractDetailView.as_view(), name="contract_detail"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("users/<int:pk>/reset-password/", views.UserResetPasswordView.as_view(), name="user_reset_password"),

    path("recode/", views.ReCodeListView.as_view(), name="recode_list"),
    path("recode/<int:pk>/", views.ReCodeDetailView.as_view(), name="recode_detail"),

    path("portfolio/projects/", AdminPortfolioProjectListView.as_view(), name="portfolio_projects"),
    path("portfolio/projects/create/", AdminPortfolioProjectCreateView.as_view(), name="portfolio_project_create"),
    path("portfolio/projects/<slug:slug>/", AdminPortfolioProjectDetailView.as_view(),
         name="portfolio_project_detail"),
    path("portfolio/projects/<slug:slug>/edit/", AdminPortfolioProjectUpdateView.as_view(),
         name="portfolio_project_edit"),
    path("portfolio/projects/<slug:slug>/delete/", AdminPortfolioProjectDeleteView.as_view(),
         name="portfolio_project_delete"),

    # categories
    path("portfolio/categories/", AdminProjectCategoryListView.as_view(), name="portfolio_categories"),
    path("portfolio/categories/create/", AdminProjectCategoryCreateView.as_view(), name="portfolio_category_create"),
    path("portfolio/categories/<int:pk>/edit/", AdminProjectCategoryUpdateView.as_view(),
         name="portfolio_category_edit"),
    path("portfolio/categories/<int:pk>/delete/", AdminProjectCategoryDeleteView.as_view(),
         name="portfolio_category_delete"),

    # roles
    path("portfolio/roles/", AdminProjectRoleListView.as_view(), name="portfolio_roles"),
    path("portfolio/roles/create/", AdminProjectRoleCreateView.as_view(), name="portfolio_role_create"),
    path("portfolio/roles/<int:pk>/edit/", AdminProjectRoleUpdateView.as_view(), name="portfolio_role_edit"),
    path("portfolio/roles/<int:pk>/delete/", AdminProjectRoleDeleteView.as_view(), name="portfolio_role_delete"),

    # child items generic CRUD (highlight/metric/step/role_assign)
    path("portfolio/projects/<slug:slug>/<str:item_type>/create/", AdminProjectChildCreateView.as_view(),
         name="portfolio_child_create"),
    path("portfolio/<str:item_type>/<int:pk>/edit/", AdminProjectChildUpdateView.as_view(),
         name="portfolio_child_edit"),
    path("portfolio/<str:item_type>/<int:pk>/delete/", AdminProjectChildDeleteView.as_view(),
         name="portfolio_child_delete"),

    path("worklog/projects/", AdminWorklogProjectListView.as_view(), name="worklog_projects"),
    path("worklog/projects/create/", AdminWorklogProjectCreateView.as_view(), name="worklog_project_create"),
    path("worklog/projects/<int:pk>/edit/", AdminWorklogProjectUpdateView.as_view(), name="worklog_project_edit"),

    path("worklog/plans/", AdminWorklogPlansListView.as_view(), name="worklog_plans"),
    path('worklog/plans/<int:pk>/', AdminDailyPlanDetailView.as_view(), name='worklog_plan_detail'),

    path('worklog/reports/', AdminWorklogReportListView.as_view(), name='worklog_reports'),
    path('worklog/reports/<int:pk>/', AdminReportDetailView.as_view(), name='worklog_report_detail'),

    path('worklog/status-overview/', AdminWorklogStatusOverview.as_view(), name='worklog_status_overview'),
]
