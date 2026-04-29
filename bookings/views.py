from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from .models import Booking
from vehicles.models import Vehicle

def is_admin(user):
    return user.is_staff or user.user_type == 'admin'

@login_required
def create_booking(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, is_available=True)
    
    if request.user.status != 'approved':
        messages.error(request, 'Your account must be approved before you can book vehicles.')
        return redirect('vehicle_detail', pk=vehicle.id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        special_requests = request.POST.get('special_requests', '')
        
        if not start_date or not end_date:
            messages.error(request, 'Please select both start and end dates.')
            return redirect('create_booking', vehicle_id=vehicle.id)
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start < datetime.now().date():
            messages.error(request, 'Start date cannot be in the past.')
            return redirect('create_booking', vehicle_id=vehicle.id)
        
        if end <= start:
            messages.error(request, 'End date must be after start date.')
            return redirect('create_booking', vehicle_id=vehicle.id)
        
        conflicting_bookings = Booking.objects.filter(
            vehicle=vehicle,
            status__in=['pending', 'confirmed'],
            start_date__lte=end,
            end_date__gte=start
        )
        
        if conflicting_bookings.exists():
            messages.error(request, 'Vehicle is not available for the selected dates.')
            return redirect('create_booking', vehicle_id=vehicle.id)
        
        total_days = (end - start).days
        total_price = total_days * vehicle.price_per_day
        
        booking = Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            start_date=start,
            end_date=end,
            special_requests=special_requests,
            total_days=total_days,
            total_price=total_price,
            status='pending',
            payment_status='pending'
        )
        
        messages.success(request, f'Booking created successfully! Total: KSh {total_price} for {total_days} days.')
        messages.info(request, 'Please complete the payment to confirm your booking.')
        return redirect('submit_payment', booking_id=booking.id)
    
    return render(request, 'bookings/create_booking.html', {'vehicle': vehicle})

@login_required
def submit_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.payment_status != 'pending':
        messages.warning(request, 'Payment already submitted or verified.')
        return redirect('booking_detail', pk=booking.id)
    
    if request.method == 'POST':
        payment_phone = request.POST.get('payment_phone')
        payment_code = request.POST.get('payment_code')
        
        if not payment_phone or not payment_code:
            messages.error(request, 'Please provide both phone number and payment code.')
            return redirect('submit_payment', booking_id=booking.id)
        
        booking.payment_phone = payment_phone
        booking.payment_code = payment_code
        booking.payment_status = 'payment_sent'
        booking.save()
        
        messages.success(request, 'Payment information submitted! Our admin will verify your payment shortly.')
        return redirect('booking_detail', pk=booking.id)
    
    return render(request, 'bookings/submit_payment.html', {'booking': booking})

@login_required
def pending_payments(request):
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('home')
    pending_bookings = Booking.objects.filter(payment_status='payment_sent')
    return render(request, 'bookings/pending_payments.html', {'pending_bookings': pending_bookings})

@login_required
def verify_payment(request, booking_id):
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'verify':
            booking.payment_status = 'verified'
            booking.status = 'confirmed'
            booking.payment_date = timezone.now()
            booking.admin_notes = admin_notes
            booking.save()
            messages.success(request, f'Payment for booking #{booking.id} has been verified and confirmed!')
            
        elif action == 'reject':
            booking.payment_status = 'failed'
            booking.status = 'cancelled'
            booking.admin_notes = admin_notes
            booking.save()
            messages.warning(request, f'Payment for booking #{booking.id} has been rejected.')
        
        return redirect('pending_payments')
    
    return render(request, 'bookings/verify_payment.html', {'booking': booking})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})

@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('my_bookings')
    
    return render(request, 'bookings/booking_detail.html', {'booking': booking})

@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if booking.status == 'pending' and booking.payment_status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel this booking.')
    
    return redirect('booking_detail', pk=booking.id)
