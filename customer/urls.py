from django.urls import path
from . import views

urlpatterns = [
    path('address/', views.customer_address_list, name='customer_address_list'),
    path('address/<int:pk>/', views.customer_address_detail, name='customer_address_detail'),
]