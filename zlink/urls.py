from django.urls import path
from . import views

app_name = 'zlink'

urlpatterns = [
    path('ReCode/', views.ReCodeView.as_view(), name='recode')

]