from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from .models import User
from bookings.models import Booking
from vehicles.models import Vehicle
import secrets
import hashlib

User = get_user_model()

# ========== AUTHENTICATION VIEWS ==========

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

# ========== ADMIN APPROVAL VIEWS ==========

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

# ========== DASHBOARD VIEWS ==========

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

# ========== PASSWORD RESET VIEWS ==========

def forgot_password(request):
    """User requests password reset"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            user.admin_message = f'RESET_REQUEST:{token_hash}'
            user.save()
            messages.success(request, 'Password reset request submitted!')
            messages.info(request, f'Your request token: {token}')
            messages.info(request, 'Please give this token to the admin for approval.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return redirect('forgot_password')
    return render(request, 'accounts/forgot_password.html')

@staff_member_required
def pending_password_resets(request):
    users_with_reset = User.objects.filter(admin_message__startswith='RESET_REQUEST:')
    pending_requests = []
    for user in users_with_reset:
        token_hash = user.admin_message.replace('RESET_REQUEST:', '')
        pending_requests.append({
            'user': user,
            'token_preview': token_hash[:20] + '...'
        })
    return render(request, 'accounts/pending_resets.html', {'pending_requests': pending_requests})

@staff_member_required
def approve_password_reset(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            reset_token = secrets.token_urlsafe(32)
            user.admin_message = f'RESET_APPROVED:{reset_token}'
            user.save()
            reset_link = request.build_absolute_uri(f'/set-new-password/{reset_token}/')
            messages.success(request, f'Password reset approved for {user.email}!')
            messages.info(request, f'Reset link for user: {reset_link}')
            messages.info(request, 'Share this link with the user so they can set their own password.')
            return redirect('pending_password_resets')
        elif action == 'reject':
            user.admin_message = ''
            user.save()
            messages.warning(request, f'Password reset request rejected for {user.email}.')
            return redirect('pending_password_resets')
    
    return render(request, 'accounts/approve_reset.html', {'user': user})

def set_new_password(request, token):
    """User sets their own new password using approved token"""
    users = User.objects.filter(admin_message__contains=token)
    user = None
    for u in users:
        if u.admin_message.endswith(token):
            user = u
            break
    
    if not user:
        messages.error(request, 'Invalid or expired reset link. Please request a new password reset.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('set_new_password', token=token)
        
        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('set_new_password', token=token)
        
        user.set_password(new_password)
        user.admin_message = f'Password reset completed by user on {timezone.now()}'
        user.save()
        
        messages.success(request, 'Password reset successful! Please login with your new password.')
        return redirect('login')
    
    return render(request, 'accounts/reset_password_form.html', {'token': token})

# ========== API VIEWS FOR DASHBOARD ==========

def dashboard_stats(request):
    stats = {
        'total_users': User.objects.count(),
        'pending_users': User.objects.filter(status='pending').count(),
        'total_bookings': Booking.objects.count(),
        'total_revenue': float(Booking.objects.filter(payment_status='verified').aggregate(Sum('total_price'))['total_price__sum'] or 0),
    }
    return JsonResponse(stats)

def recent_users(request):
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

def recent_payments(request):
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
            } for p in payments
        ]
    }
    return JsonResponse(data)

def pending_payments_count(request):
    count = Booking.objects.filter(payment_status='payment_sent').count()
    return JsonResponse({'count': count})

def pending_resets_count(request):
    count = User.objects.filter(admin_message__startswith='RESET_REQUEST:').count()
    return JsonResponse({'count': count})

def customer_stats(request):
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
# Add this import at the top
from django.core.mail import send_mail
from django.conf import settings

@staff_member_required
def approve_password_reset(request, user_id):
    """Admin approves password reset - sends link directly to customer's email"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Generate a secure reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store the token with user
            user.admin_message = f'RESET_APPROVED:{reset_token}'
            user.save()
            
            # Generate reset link for customer
            reset_link = request.build_absolute_uri(f'/set-new-password/{reset_token}/')
            
            # Send email DIRECTLY TO CUSTOMER
            try:
                send_mail(
                    subject='Password Reset Approved - AutoRent',
                    message=f'''
Dear {user.username},

Your password reset request has been approved!

Click the link below to set your new password:
{reset_link}

This link will expire after one use.

If you did not request this, please ignore this email.

Best regards,
AutoRent Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],  # Email goes to CUSTOMER
                    fail_silently=False,
                )
                messages.success(request, f'✓ Password reset approved!')
                messages.success(request, f'✓ Reset link sent to customer: {user.email}')
                
            except Exception as e:
                messages.warning(request, f'Email failed to send. Please share this link with the customer:')
                messages.info(request, f'{reset_link}')
            
            return redirect('pending_password_resets')
            
        elif action == 'reject':
            # Send rejection notice to customer
            try:
                send_mail(
                    subject='Password Reset Request Denied - AutoRent',
                    message=f'''
Dear {user.username},

Your password reset request has been denied.

Please contact support for assistance.

Best regards,
AutoRent Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except:
                pass
            
            user.admin_message = ''
            user.save()
            messages.warning(request, f'Password reset request rejected for {user.email}.')
            return redirect('pending_password_resets')
    
    return render(request, 'accounts/approve_reset.html', {'user': user})
