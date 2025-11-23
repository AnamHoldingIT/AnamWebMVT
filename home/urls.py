from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('' , views.HomeView.as_view() , name='home' ),
    path('contract/create/', views.ContractCreateView.as_view(), name='contract_create'),
]