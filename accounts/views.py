from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import User
from django.http import JsonResponse
from bookings.models import Booking
from vehicles.models import Vehicle
from django.db.models import Sum, Count
import secrets

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        if not email or not username or not password1:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('signup')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return redirect('signup')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                phone=phone or '',
                address=address or '',
                status='pending'
            )
            messages.success(request, 'Registration successful! Please wait for admin approval.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('signup')
    
    return render(request, 'accounts/signup.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return redirect('login')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_staff or user.user_type == 'admin':
                login(request, user)
                messages.success(request, f'Welcome Admin, {user.email}!')
                return redirect('admin_dashboard')
            elif user.user_type == 'customer':
                login(request, user)
                if user.status == 'approved':
                    messages.success(request, f'Welcome back, {user.email}!')
                    return redirect('customer_dashboard')
                elif user.status == 'pending':
                    messages.warning(request, 'Your account is pending admin approval.')
                elif user.status == 'rejected':
                    messages.error(request, f'Account rejected. Reason: {user.admin_message}')
            else:
                messages.error(request, 'Invalid user type.')
        else:
            messages.error(request, 'Invalid email or password!')
        
        return redirect('login')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@staff_member_required
def pending_users(request):
    pending_users = User.objects.filter(status='pending')
    return render(request, 'accounts/pending_users.html', {'pending_users': pending_users})

@staff_member_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        message = request.POST.get('message', '')
        
        if action == 'approve':
            user.status = 'approved'
            if not message:
                message = 'Your account has been approved! You can now log in.'
            user.admin_message = message
            user.save()
            messages.success(request, f'User {user.email} has been approved.')
            return redirect('pending_users')
        elif action == 'reject':
            user.status = 'rejected'
            if not message:
                message = 'Your account has been rejected. Contact support.'
            user.admin_message = message
            user.save()
            messages.warning(request, f'User {user.email} has been rejected.')
            return redirect('pending_users')
    
    return render(request, 'accounts/approve_user.html', {'user': user})

@login_required
def admin_dashboard(request):
    if not request.user.is_staff and request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def customer_dashboard(request):
    if request.user.user_type != 'customer':
        messages.error(request, 'Access denied. Customer only.')
        return redirect('home')
    return render(request, 'accounts/customer_dashboard.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            user.admin_message = f'RESET_TOKEN:{token}'
            user.save()
            messages.success(request, 'Password reset requested. Admin will review.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Email not found.')
    return render(request, 'accounts/forgot_password.html')

@staff_member_required
def pending_password_resets(request):
    users_with_reset = User.objects.filter(admin_message__startswith='RESET_TOKEN:')
    return render(request, 'accounts/pending_resets.html', {'users': users_with_reset})

@staff_member_required
def approve_password_reset(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.admin_message = 'Password reset approved'
            user.save()
            messages.success(request, f'Password reset for {user.email} approved!')
            return redirect('pending_password_resets')
        else:
            messages.error(request, 'Passwords do not match!')
    return render(request, 'accounts/approve_reset.html', {'user': user})

def dashboard_stats(request):
    """Admin dashboard statistics"""
    stats = {
        'total_users': User.objects.count(),
        'pending_users': User.objects.filter(status='pending').count(),
        'total_bookings': Booking.objects.count(),
        'total_revenue': Booking.objects.filter(payment_status='verified').aggregate(Sum('total_price'))['total_price__sum'] or 0,
    }
    return JsonResponse(stats)

def recent_users(request):
    """Recent user registrations"""
    users = User.objects.order_by('-created_at')[:10]
    data = {
        'users': [
            {
                'username': u.username,
                'email': u.email,
                'status': u.status,
                'created_at': u.created_at.strftime('%Y-%m-%d %H:%M')
            } for u in users
        ]
    }
    return JsonResponse(data)

def recent_bookings(request):
    """Recent bookings for admin"""
    bookings = Booking.objects.select_related('user', 'vehicle').order_by('-created_at')[:10]
    data = {
        'bookings': [
            {
                'id': b.id,
                'user_email': b.user.email,
                'vehicle_name': b.vehicle.name,
                'total_price': float(b.total_price),
                'start_date': b.start_date.strftime('%Y-%m-%d'),
                'end_date': b.end_date.strftime('%Y-%m-%d'),
                'status': b.status,
                'payment_status': b.payment_status
            } for b in bookings
        ]
    }
    return JsonResponse(data)

def customer_stats(request):
    """Customer dashboard statistics"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    bookings = Booking.objects.filter(user=request.user)
    stats = {
        'total_bookings': bookings.count(),
        'active_bookings': bookings.filter(status='confirmed').count(),
        'total_spent': float(bookings.filter(payment_status='verified').aggregate(Sum('total_price'))['total_price__sum'] or 0),
    }
    return JsonResponse(stats)

def customer_bookings(request):
    """Recent bookings for customer"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:5]
    data = {
        'bookings': [
            {
                'id': b.id,
                'vehicle_name': b.vehicle.name,
                'vehicle_model': b.vehicle.model,
                'total_price': float(b.total_price),
                'total_days': b.total_days,
                'start_date': b.start_date.strftime('%Y-%m-%d'),
                'end_date': b.end_date.strftime('%Y-%m-%d'),
                'status': b.status,
                'payment_status': b.payment_status
            } for b in bookings
        ]
    }
    return JsonResponse(data)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import HttpResponse
from django.shortcuts import render, redirect

def generate_reset_link(request, email):
    """Generate a password reset link for a specific email"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(email=email)
        
        # Generate reset token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        reset_link = f"https://phelotrans-booking.onrender.com/reset-password/{uid}/{token}/"
        
        return HttpResponse(f"""
        <h2>Password Reset Link Generated</h2>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Reset Link:</strong></p>
        <p><a href="{reset_link}" target="_blank">{reset_link}</a></p>
        <p>⚠️ This link is valid for one-time use only.</p>
        <p><a href="/admin/">Back to Admin</a></p>
        """)
    except User.DoesNotExist:
        return HttpResponse(f"<h2>User with email {email} not found</h2>")

def reset_password_confirm(request, uidb64, token):
    """Confirm password reset and set new password"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                return HttpResponse("""
                <h2>✅ Password Reset Successful!</h2>
                <p>Your password has been changed.</p>
                <p><a href="/login/">Click here to login</a></p>
                """)
        
        return render(request, 'accounts/reset_password.html', {'user': user})
    else:
        return HttpResponse("<h2>Invalid or expired reset link</h2>")

def recent_payments(request):
    """Recent payments for admin dashboard"""
    from bookings.models import Booking
    payments = Booking.objects.filter(payment_status__in=['payment_sent', 'verified']).order_by('-updated_at')[:10]
    data = {
        'payments': [
            {
                'booking_id': p.id,
                'user_email': p.user.email,
                'amount': float(p.total_price),
                'payment_status': p.payment_status,
                'payment_phone': p.payment_phone,
                'payment_code': p.payment_code,
                'updated_at': p.updated_at.strftime('%Y-%m-%d %H:%M')
            } for p in payments
        ]
    }
    return JsonResponse(data)

def pending_payments_count(request):
    """Get count of pending payments for badge"""
    from bookings.models import Booking
    count = Booking.objects.filter(payment_status='payment_sent').count()
    return JsonResponse({'count': count})

def pending_resets_count(request):
    """Get count of pending password reset requests"""
    from .models import User
    count = User.objects.filter(admin_message__startswith='RESET_TOKEN:').count()
    return JsonResponse({'count': count})
