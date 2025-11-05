from django.contrib import admin
from .models import Coupon, Booking, PendingRequests, FCMToken

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'discount_value', 'is_active', 'used_count', 'usage_limit', 'valid_from', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'used_count', 'created_at', 'updated_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['code', 'name', 'description']
        }),
        ('Discount Details', {
            'fields': ['discount_type', 'discount_value', 'minimum_order_amount', 'maximum_discount_amount']
        }),
        ('Usage Limits', {
            'fields': ['usage_limit', 'used_count']
        }),
        ('Validity', {
            'fields': ['is_active', 'valid_from', 'valid_until']
        }),
        ('System Info', {
            'fields': ['id', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'therapist', 'status', 'subtotal', 'coupon_discount', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__name', 'customer__email', 'therapist__name', 'therapist__email']
    readonly_fields = ['id', 'created_at']

@admin.register(PendingRequests)
class PendingRequestsAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name']
    readonly_fields = ['id', 'created_at']

@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token']
    search_fields = ['user__name', 'user__email']
