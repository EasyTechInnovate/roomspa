from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # =================== AUTHENTICATION APIs ===================
    path('api/auth/login/', views.admin_login_api, name='admin_login_api'),
    path('api/auth/logout/', views.admin_logout_api, name='admin_logout_api'),

    # =================== DASHBOARD APIs ===================
    path('api/dashboard/', views.dashboard_overview_api, name='dashboard_overview_api'),

    # =================== USER MANAGEMENT APIs ===================
    path('api/users/', views.users_list_api, name='users_list_api'),
    path('api/users/<int:user_id>/', views.user_detail_api, name='user_detail_api'),

    # =================== BOOKING MANAGEMENT APIs ===================
    path('api/bookings/', views.bookings_list_api, name='bookings_list_api'),
    path('api/bookings/<uuid:booking_id>/', views.booking_detail_api, name='booking_detail_api'),

    # =================== ANALYTICS APIs ===================
    path('api/analytics/bookings/', views.booking_analytics_api, name='booking_analytics_api'),
    path('api/analytics/therapists/', views.therapist_analytics_api, name='therapist_analytics_api'),

    # =================== FINANCIAL REPORTS APIs ===================
    path('api/reports/financial/', views.financial_reports_api, name='financial_reports_api'),

    # =================== LIVE MONITORING APIs ===================
    path('api/monitoring/', views.live_monitoring_api, name='live_monitoring_api'),

    # =================== SYSTEM HEALTH APIs ===================
    path('api/system/health/', views.system_health_api, name='system_health_api'),

    # =================== USER MANAGEMENT ACTIONS ===================
    path('api/users/<int:user_id>/action/', views.user_action_api, name='user_action_api'),

    # =================== BOOKING MANAGEMENT ACTIONS ===================
    path('api/bookings/<uuid:booking_id>/action/', views.booking_action_api, name='booking_action_api'),

    # =================== THERAPIST MANAGEMENT ===================
    path('api/therapists/', views.therapist_list_api, name='therapist_list_api'),
    path('api/therapists/<int:therapist_id>/action/', views.therapist_action_api, name='therapist_action_api'),

    # =================== CUSTOMER MANAGEMENT ===================
    path('api/customers/', views.customer_list_api, name='customer_list_api'),

    # =================== PENDING REQUESTS MANAGEMENT ===================
    path('api/pending-requests/', views.pending_requests_api, name='pending_requests_api'),
    path('api/pending-requests/<uuid:request_id>/action/', views.pending_request_action_api, name='pending_request_action_api'),

    # =================== CHAT/COMMUNICATION MANAGEMENT ===================
    path('api/conversations/', views.conversations_api, name='conversations_api'),
    path('api/conversations/<uuid:conversation_id>/messages/', views.conversation_messages_api, name='conversation_messages_api'),

    # =================== ADVANCED ANALYTICS ===================
    path('api/analytics/advanced/', views.advanced_analytics_api, name='advanced_analytics_api'),

    # =================== EXPORT AND REPORTING ===================
    path('api/export/', views.export_data_api, name='export_data_api'),

    # =================== NOTIFICATION MANAGEMENT ===================
    path('api/notifications/tokens/', views.fcm_tokens_api, name='fcm_tokens_api'),
    path('api/notifications/send/', views.send_notification_api, name='send_notification_api'),

    # =================== COUPON MANAGEMENT ===================
    path('api/coupons/', views.admin_coupons_list_api, name='admin_coupons_list_api'),
    path('api/coupons/create/', views.admin_coupons_create_api, name='admin_coupons_create_api'),
    path('api/coupons/<uuid:coupon_id>/', views.admin_coupons_detail_api, name='admin_coupons_detail_api'),
    path('api/coupons/<uuid:coupon_id>/update/', views.admin_coupons_update_api, name='admin_coupons_update_api'),
    path('api/coupons/<uuid:coupon_id>/delete/', views.admin_coupons_delete_api, name='admin_coupons_delete_api'),
    path('api/coupons/<uuid:coupon_id>/toggle-status/', views.admin_coupons_toggle_status_api, name='admin_coupons_toggle_status_api'),
    path('api/coupons/stats/', views.admin_coupons_stats_api, name='admin_coupons_stats_api'),
]