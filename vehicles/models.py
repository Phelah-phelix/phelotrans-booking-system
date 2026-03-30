from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class VehicleCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name_plural = "Vehicle Categories"
    
    def __str__(self):
        return self.name

class Vehicle(models.Model):
    TRANSMISSION_CHOICES = (
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    )
    
    FUEL_TYPE_CHOICES = (
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    )
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(VehicleCategory, on_delete=models.SET_NULL, related_name='vehicles', null=True, blank=True)
    model = models.CharField(max_length=100)
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2025)])
    license_plate = models.CharField(max_length=20, unique=True)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)
    seats = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    features = models.TextField(blank=True, help_text="Comma-separated features")
    main_image = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.license_plate})"
    
    def get_features_list(self):
        return [f.strip() for f in self.features.split(',') if f.strip()]

class VehicleImage(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicles/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"Image for {self.vehicle.name}"

class VehicleReview(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['vehicle', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.vehicle.name} by {self.user.email}"
