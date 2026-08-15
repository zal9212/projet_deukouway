import django_filters
from apps.properties.models import Property

class PropertyFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name='city', lookup_expr='icontains')
    district = django_filters.CharFilter(field_name='district', lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    bedrooms = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='gte')
    bathrooms = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='gte')
    surface = django_filters.NumberFilter(field_name='surface', lookup_expr='gte')
    property_type = django_filters.CharFilter(field_name='property_type__slug', lookup_expr='exact')

    class Meta:
        model = Property
        fields = ['city', 'district', 'min_price', 'max_price', 'bedrooms', 'bathrooms', 'surface', 'property_type', 'status']
