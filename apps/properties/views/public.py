from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from apps.properties.services.selectors import PropertySelector
from apps.properties.models import Property

class PropertySearchView(ListView):
    template_name = 'pages/public/search.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        # We rely strictly on the selector
        queryset = PropertySelector.get_available_properties()
        
        # Filtering logic could be handled here or inside a specific selector method.
        # Example filters (in a real app we'd build a filter dictionary):
        city = self.request.GET.get('city')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset

class PropertyDetailView(DetailView):
    template_name = 'pages/public/property_detail.html'
    context_object_name = 'property'

    def get_object(self):
        property_id = self.kwargs.get('pk')
        return PropertySelector.get_property_by_id(property_id)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Using selector for related data like photos, features
        context['photos'] = PropertySelector.get_property_photos(self.object)
        context['amenities'] = PropertySelector.get_property_amenities(self.object)
        return context
