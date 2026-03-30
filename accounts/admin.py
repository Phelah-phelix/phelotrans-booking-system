from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'status', 'user_type', 'created_at')
    list_filter = ('status', 'user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'phone')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Account Status', {
            'fields': ('user_type', 'status', 'admin_message')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address', 'profile_picture')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Account Status', {
            'fields': ('user_type', 'status')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
    )

admin.site.register(User, CustomUserAdmin)
