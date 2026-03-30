from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import User

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # Validation
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
        
        # Create user with pending status
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
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.status == 'approved':
                login(request, user)
                messages.success(request, f'Welcome back, {user.email}!')
                return redirect('home')
            elif user.status == 'pending':
                messages.warning(request, 'Your account is pending admin approval. You will be notified once approved.')
            elif user.status == 'rejected':
                messages.error(request, f'Your account has been rejected. Reason: {user.admin_message}')
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
                message = 'Your account has been approved! You can now log in and book vehicles.'
            user.admin_message = message
            user.save()
            messages.success(request, f'User {user.email} has been approved.')
            return redirect('pending_users')
            
        elif action == 'reject':
            user.status = 'rejected'
            if not message:
                message = 'Your account has been rejected. Please contact support for more information.'
            user.admin_message = message
            user.save()
            messages.warning(request, f'User {user.email} has been rejected.')
            return redirect('pending_users')
        else:
            messages.error(request, 'Invalid action!')
            return redirect('pending_users')
    
    return render(request, 'accounts/approve_user.html', {'user': user})
