import django_filters
from apps.reservations.models import ReservationRequest

class ReservationRequestFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    property_id = django_filters.UUIDFilter(field_name='property_id')
    check_in_after = django_filters.DateFilter(field_name='check_in', lookup_expr='gte')
    check_out_before = django_filters.DateFilter(field_name='check_out', lookup_expr='lte')

    class Meta:
        model = ReservationRequest
        fields = ['status', 'property_id', 'check_in_after', 'check_out_before']
