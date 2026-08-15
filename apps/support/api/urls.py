from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.support.api.viewsets import SupportCategoryViewSet, SupportTicketViewSet

router = DefaultRouter()
router.register(r'categories', SupportCategoryViewSet, basename='support-category')
router.register(r'tickets', SupportTicketViewSet, basename='support-ticket')

urlpatterns = [
    path('', include(router.urls)),
]
