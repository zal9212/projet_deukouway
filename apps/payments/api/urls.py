from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.payments.api.viewsets import PaymentViewSet, InvoiceViewSet, PayoutViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payouts', PayoutViewSet, basename='payout')
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
