from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

class UserProfileAdmin(UserAdmin):
    model = UserProfile
    list_display = ('name', 'email', 'phone_number', 'role', 'gender', 'consent', 'verification_status', 'is_active')
    list_filter = ('role', 'gender', 'consent', 'verification_status', 'is_active')
    fieldsets = (
        (None, {'fields': ('name', 'email', 'phone_number', 'password')}),
        ('Personal Info', {
            'fields': ('gender', 'role', 'consent')
        }),
        ('Verification', {'fields': ('verification_status', 'verification_token')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_created')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'name', 'email', 'phone_number', 'password1', 'password2',
                'gender', 'role', 'consent', 'is_staff', 'is_active'
            )
        }),
    )
    search_fields = ('name', 'email', 'phone_number')
    ordering = ('name', 'email')

admin.site.register(UserProfile, UserProfileAdmin)