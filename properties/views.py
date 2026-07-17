from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from .models import Property, PropertyImage, Amenity
from .forms import PropertyForm
from django.contrib import messages

class PropertiesListView(ListView):
    """
    List view for properties with filters and HTMX partial rendering support.
    """
    model = Property
    template_name = 'pages/public/search.html'
    context_object_name = 'properties'

    def get_queryset(self):
        queryset = Property.objects.filter(status='approved')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(city__icontains=search) |
                Q(neighborhood__icontains=search)
            )
            
        property_type = self.request.GET.get('type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
            
        price_max = self.request.GET.get('price_max')
        if price_max:
            queryset = queryset.filter(price_per_night__lte=price_max)
            
        capacity = self.request.GET.get('capacity')
        if capacity:
            queryset = queryset.filter(capacity__gte=capacity)
            
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__iexact=city)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties = self.get_queryset()
        
        map_properties = []
        for prop in properties:
            img_url = ""
            main_img = prop.images.filter(is_main=True).first() or prop.images.first()
            if main_img:
                img_url = main_img.image.url
            
            map_properties.append({
                'id': prop.id,
                'title': prop.title,
                'price': int(prop.price_per_night),
                'lat': prop.latitude,
                'lng': prop.longitude,
                'image': img_url,
                'city': prop.city,
                'neighborhood': prop.neighborhood,
                'detail_url': reverse('property_detail', kwargs={'pk': prop.id})
            })
            
        context['map_properties_json'] = map_properties
        context['amenities'] = Amenity.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.headers.get('HX-Request'):
            context = self.get_context_data()
            return render(request, 'properties/partials/property_cards.html', context)
        return super().get(request, *args, **kwargs)


class PropertyDetailView(DetailView):
    """
    Detailed listing view with booking form integration and interactive maps.
    """
    model = Property
    template_name = 'pages/public/property_detail.html'
    context_object_name = 'property'


class OwnerOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Permission class checking owner role and verification status.
    """
    def test_func(self):
        return self.request.user.role == 'owner' and self.request.user.is_verified_owner

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if self.request.user.role == 'owner':
                messages.warning(self.request, "Votre compte propriétaire n'est pas encore validé par un administrateur.")
                return redirect('profile')
            messages.error(self.request, "Accès réservé aux propriétaires.")
            return redirect('home')
        messages.error(self.request, "Veuillez vous connecter pour accéder à cette page.")
        return redirect('login')


class PropertyCreateView(OwnerOnlyMixin, CreateView):
    """
    Form view for Owners to create new property listings.
    """
    model = Property
    form_class = PropertyForm
    template_name = 'pages/owner/add_property.html'
    success_url = reverse_lazy('owner_dashboard')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.status = 'pending'  # Force admin validation
        response = super().form_valid(form)
        
        # Save multiple uploads
        images = self.request.FILES.getlist('images')
        for i, img in enumerate(images):
            PropertyImage.objects.create(
                property=self.object,
                image=img,
                is_main=(i == 0)
            )
        messages.success(self.request, "Votre logement a été soumis pour modération.")
        return response


class PropertyUpdateView(OwnerOnlyMixin, UpdateView):
    """
    Form view for Owners to update listing details.
    """
    model = Property
    form_class = PropertyForm
    template_name = 'pages/owner/add_property.html'
    success_url = reverse_lazy('owner_dashboard')

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        form.instance.status = 'pending'  # Require validation again on changes
        response = super().form_valid(form)
        
        images = self.request.FILES.getlist('images')
        for img in images:
            PropertyImage.objects.create(
                property=self.object,
                image=img,
                is_main=False
            )
        messages.success(self.request, "Votre logement a été modifié et repasse en modération.")
        return response


class PropertyDeleteView(OwnerOnlyMixin, DeleteView):
    """
    Delete listing view restricted to the owner of the listing.
    """
    model = Property
    template_name = 'pages/owner/property_confirm_delete.html'
    success_url = reverse_lazy('owner_dashboard')

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Logement supprimé avec succès.")
        return super().delete(request, *args, **kwargs)
