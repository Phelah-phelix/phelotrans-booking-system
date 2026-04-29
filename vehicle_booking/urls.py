from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('login/', accounts_views.login_view, name='login'),
    path('signup/', accounts_views.signup_view, name='signup'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('pending-users/', accounts_views.pending_users, name='pending_users'),
    path('approve-user/<int:user_id>/', accounts_views.approve_user, name='approve_user'),
    path('vehicles/', include('vehicles.urls')),
    path('bookings/', include('bookings.urls')),
    path('mpesa/', include('mpesa_payments.urls')),
    path('accounts/', include('allauth.urls')),
    #API ENDPOINT for admin dashboard
    path('admin-dashboard/', accounts_views.admin_dashboard, name='admin_dashboard'),
    path('customer-dashboard/', accounts_views.customer_dashboard, name='customer_dashboard'),
    path('forgot-password/', accounts_views.forgot_password, name='forgot_password'),
    path('pending-resets/', accounts_views.pending_password_resets, name='pending_password_resets'),
    path('approve-reset/<int:user_id>/', accounts_views.approve_password_reset, name='approve_password_reset'),
    #API End pint for dashboard
    path('api/dashboard-stats/', accounts_views.dashboard_stats, name='dashboard_stats'),
    path('api/recent-users/', accounts_views.recent_users, name='recent_users'),
    path('api/recent-bookings/', accounts_views.recent_bookings, name='recent_bookings'),
    path('api/customer-stats/', accounts_views.customer_stats, name='customer_stats'),
    path('api/customer-bookings/', accounts_views.customer_bookings, name='customer_bookings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API Endpoints for Dashboards
path('api/dashboard-stats/', accounts_views.dashboard_stats, name='dashboard_stats'),
path('api/recent-users/', accounts_views.recent_users, name='recent_users'),
path('api/recent-bookings/', accounts_views.recent_bookings, name='recent_bookings'),
path('api/customer-stats/', accounts_views.customer_stats, name='customer_stats'),
path('api/customer-bookings/', accounts_views.customer_bookings, name='customer_bookings'),
