from django.urls import path
from . import views

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
]
