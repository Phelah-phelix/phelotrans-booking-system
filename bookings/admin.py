from django.contrib import admin
from .models import Booking

class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vehicle', 'start_date', 'end_date', 'total_price', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'start_date')
    search_fields = ('user__email', 'vehicle__name', 'vehicle__license_plate')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('total_days', 'total_price', 'created_at')
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'vehicle', 'start_date', 'end_date', 'total_days', 'total_price')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Additional', {
            'fields': ('special_requests', 'created_at', 'updated_at')
        }),
    )

admin.site.register(Booking, BookingAdmin)
