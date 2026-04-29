from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from bookings.models import Booking
from .services.mpesa_service import MpesaService
import json
import logging
import random

logger = logging.getLogger(__name__)

# Initialize Mpesa service only if credentials exist
def get_mpesa_service():
    try:
        return MpesaService()
    except Exception as e:
        logger.warning(f"M-Pesa service not available: {str(e)}")
        return None

@login_required
def initiate_mpesa_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.payment_status != 'pending':
        messages.warning(request, 'Payment already processed.')
        return redirect('booking_detail', pk=booking.id)
    
    # Check if M-Pesa is configured
    has_credentials = getattr(settings, 'DARAJAA_CONSUMER_KEY', '') and getattr(settings, 'DARAJAA_CONSUMER_SECRET', '')
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, 'Please provide your M-Pesa phone number')
            return redirect('initiate_mpesa_payment', booking_id=booking.id)
        
        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        if has_credentials and get_mpesa_service():
            # Real STK Push
            callback_url = getattr(settings, 'DARAJAA_CALLBACK_URL', 'https://your-domain.com/mpesa/callback/')
            
            mpesa = get_mpesa_service()
            response = mpesa.stk_push(
                phone_number=phone_number,
                amount=float(booking.total_price),
                account_reference=f'BK{booking.id}',
                transaction_desc=f'Vehicle Booking',
                callback_url=callback_url
            )
            
            if response.get('error'):
                messages.error(request, f'Payment initiation failed: {response["error"]}')
                return redirect('booking_detail', pk=booking.id)
            
            checkout_request_id = response.get('CheckoutRequestID')
            if checkout_request_id:
                booking.payment_code = checkout_request_id
                booking.payment_phone = phone_number
                booking.payment_status = 'payment_sent'
                booking.save()
                
                messages.success(request, 'STK Push sent! Please check your phone and enter PIN.')
                return redirect('mpesa_status', booking_id=booking.id)
            else:
                messages.error(request, f'Failed: {response.get("ResponseDescription", "Unknown error")}')
                return redirect('booking_detail', pk=booking.id)
        else:
            # Test/Simulation mode
            test_code = f"TEST{random.randint(100000, 999999)}"
            
            booking.payment_code = test_code
            booking.payment_phone = phone_number
            booking.payment_status = 'payment_sent'
            booking.save()
            
            messages.warning(request, '⚠️ TEST MODE: M-Pesa not configured!')
            messages.info(request, f'📱 Phone: {phone_number} | Test Code: {test_code}')
            messages.info(request, 'In production, you would receive an STK Push on your phone.')
            messages.info(request, 'Admin can verify this test payment using the code above.')
            
            return redirect('mpesa_status', booking_id=booking.id)
    
    # Show configuration warning if credentials missing
    if not has_credentials:
        messages.warning(request, '⚠️ M-Pesa not configured. Add Daraja credentials to settings.py for real payments.')
        messages.info(request, 'Currently in TEST MODE. Admin can manually verify payments.')
    
    return render(request, 'mpesa_payments/initiate_payment.html', {'booking': booking})

@login_required
def mpesa_payment_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'mpesa_payments/payment_status.html', {'booking': booking})

@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle M-Pesa callback"""
    try:
        data = json.loads(request.body)
        logger.info(f"M-Pesa Callback received")
        
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_desc = stk_callback.get('ResultDesc')
        
        booking = Booking.objects.filter(payment_code=checkout_request_id).first()
        
        if booking:
            if result_code == '0':
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        booking.admin_notes = f"M-Pesa Receipt: {item.get('Value')}"
                        break
                
                booking.payment_status = 'verified'
                booking.status = 'confirmed'
                booking.payment_date = timezone.now()
                booking.save()
                
                logger.info(f"Payment verified for booking {booking.id}")
            else:
                booking.payment_status = 'failed'
                booking.status = 'cancelled'
                booking.admin_notes = f"Payment failed: {result_desc}"
                booking.save()
                
                logger.warning(f"Payment failed for booking {booking.id}: {result_desc}")
        
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)}, status=500)
