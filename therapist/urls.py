from django.urls import path
from . import views

urlpatterns = [
    path('location/', views.location_view, name='therapist_location'),
    path('services/', views.services_view, name='therapist_services'),
    path('bank-details/', views.bank_details_list, name='therapist_bank_details_list'),
    path('bank-details/<int:pk>/', views.bank_details_detail, name='therapist_bank_details_detail'),
    path('status/', views.update_therapist_status, name='therapist-status-update'),
]