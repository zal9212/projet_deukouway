from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.dashboard.api.viewsets import DashboardViewSet

router = DefaultRouter()
router.register(r'', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
