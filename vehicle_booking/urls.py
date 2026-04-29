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
    path('admin-dashboard/', accounts_views.admin_dashboard, name='admin_dashboard'),
    path('customer-dashboard/', accounts_views.customer_dashboard, name='customer_dashboard'),
    path('forgot-password/', accounts_views.forgot_password, name='forgot_password'),
    path('pending-resets/', accounts_views.pending_password_resets, name='pending_password_resets'),
    path('approve-reset/<int:user_id>/', accounts_views.approve_password_reset, name='approve_password_reset'),
    path('generate-reset/<str:email>/', accounts_views.generate_reset_link, name='generate_reset'),
    path('reset-password/<uidb64>/<token>/', accounts_views.reset_password_confirm, name='reset_confirm'),
    path('api/recent-payments/', accounts_views.recent_payments, name='recent_payments'),
    path('api/pending-payments-count/', accounts_views.pending_payments_count, name='pending_payments_count'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    path('api/pending-resets-count/', accounts_views.pending_resets_count, name='pending_resets_count'),
