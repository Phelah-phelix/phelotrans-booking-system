from django.db import models
from datetime import date

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(editable=False, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days
            self.total_price = self.total_days * self.vehicle.price_per_day
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.email} - {self.vehicle.name}"
    
    class Meta:
        ordering = ['-created_at']
