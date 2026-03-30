from django.contrib import admin
from .models import VehicleCategory, Vehicle, VehicleImage, VehicleReview

class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1

class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'model', 'price_per_day', 'is_available', 'is_featured')
    list_filter = ('is_available', 'is_featured', 'transmission', 'fuel_type', 'category')
    search_fields = ('name', 'model', 'license_plate')
    list_editable = ('is_available', 'is_featured')
    inlines = [VehicleImageInline]

class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class VehicleReviewAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('vehicle__name', 'user__email')

admin.site.register(VehicleCategory, VehicleCategoryAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(VehicleReview, VehicleReviewAdmin)
