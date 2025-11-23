from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('admin-login/' , views.AdminLoginView.as_view(), name='admin_login'),
    path("logout/", views.AdminLogoutView.as_view(), name="logout"),
    path("user-login/" , views.UserLoginView.as_view() , name='user_login')
]