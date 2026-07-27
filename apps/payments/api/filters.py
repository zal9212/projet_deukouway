import django_filters
from apps.payments.models import Payment

class PaymentFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    method = django_filters.CharFilter(field_name='method', lookup_expr='exact')
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = Payment
        fields = ['status', 'method', 'min_amount', 'max_amount']
