from django.urls import path
from . import views

urlpatterns = [
    path('', views.VehicleListView.as_view(), name='vehicle_list'),
    path('<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('bulk-update/', views.bulk_update_quantity, name='bulk_update_quantity'),
]
