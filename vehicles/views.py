from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from .models import Vehicle, VehicleCategory

class VehicleListView(ListView):
    model = Vehicle
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 9
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Vehicle.objects.filter(is_available=True).order_by('-created_at')
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price_per_day__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_per_day__lte=max_price)
        
        transmission = self.request.GET.get('transmission')
        if transmission:
            queryset = queryset.filter(transmission=transmission)
        
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

@staff_member_required
def bulk_update_quantity(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        additional_quantity = int(request.POST.get('additional_quantity', 0))
        
        vehicles = Vehicle.objects.filter(category_id=category_id)
        for vehicle in vehicles:
            vehicle.quantity_available += additional_quantity
            vehicle.save()
        
        messages.success(request, f'Added {additional_quantity} units to all vehicles in category')
        return redirect('admin_dashboard')
    
    categories = VehicleCategory.objects.all()
    return render(request, 'vehicles/bulk_update.html', {'categories': categories})
