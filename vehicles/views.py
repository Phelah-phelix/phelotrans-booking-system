from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Vehicle, VehicleCategory

class VehicleListView(ListView):
    model = Vehicle
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 9
    ordering = ['-created_at']  # Add ordering to fix the warning
    
    def get_queryset(self):
        queryset = Vehicle.objects.filter(is_available=True).order_by('-created_at')
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Price filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price_per_day__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_per_day__lte=max_price)
        
        # Transmission filter
        transmission = self.request.GET.get('transmission')
        if transmission:
            queryset = queryset.filter(transmission=transmission)
        
        # Seats filter
        seats = self.request.GET.get('seats')
        if seats:
            queryset = queryset.filter(seats__gte=seats)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = VehicleCategory.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        return context

def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'vehicles/vehicle_detail.html', {'vehicle': vehicle})
