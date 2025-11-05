from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('search-therapists/', views.search_therapists_view, name='search_therapists'),
    path('register-fcm-token/', views.register_fcm_token, name='register_fcm_token'),
    path('send-booking-request/', views.send_booking_request, name='send_booking_request'),
    path('respond-to-booking-request/', views.respond_to_booking_request, name='respond_to_booking_request'),
    path('bookings/', views.list_bookings, name='list_bookings'),
    path('bookings/<uuid:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('bookings/<uuid:booking_id>/update-status/', views.update_booking_status, name='update_booking_status'),
    path('pending-requests/', views.pending_requests_list, name='pending_requests_list'),
    path('analytics/', views.therapist_analytics, name='therapist_analytics'),
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
]