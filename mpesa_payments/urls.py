from django.urls import path
from . import views

urlpatterns = [
    path('initiate/<int:booking_id>/', views.initiate_mpesa_payment, name='initiate_mpesa_payment'),
    path('status/<int:booking_id>/', views.mpesa_payment_status, name='mpesa_status'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]