from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reservations.api.viewsets import ReservationRequestViewSet, ReservationViewSet

router = DefaultRouter()
router.register(r'requests', ReservationRequestViewSet, basename='reservation-request')
router.register(r'confirmed', ReservationViewSet, basename='reservation-confirmed')

urlpatterns = [
    path('', include(router.urls)),
]
