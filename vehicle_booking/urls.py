from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', accounts_views.login_view, name='login'),
    path('signup/', accounts_views.signup_view, name='signup'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('pending-users/', accounts_views.pending_users, name='pending_users'),
    path('approve-user/<int:user_id>/', accounts_views.approve_user, name='approve_user'),
    path('vehicles/', include('vehicles.urls')),
    path('bookings/', include('bookings.urls')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
