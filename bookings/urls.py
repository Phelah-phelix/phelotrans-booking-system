from django.urls import path
from . import views

urlpatterns = [
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('create/<int:vehicle_id>/', views.create_booking, name='create_booking'),
    path('submit-payment/<int:booking_id>/', views.submit_payment, name='submit_payment'),
    path('pending-payments/', views.pending_payments, name='pending_payments'),
    path('verify-payment/<int:booking_id>/', views.verify_payment, name='verify_payment'),
    path('<int:pk>/', views.booking_detail, name='booking_detail'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]
