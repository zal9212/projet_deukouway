from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.properties.api.viewsets import (
    PropertyViewSet, PropertyCategoryViewSet, PropertyTypeViewSet, FavoriteViewSet
)

router = DefaultRouter()
router.register(r'categories', PropertyCategoryViewSet, basename='category')
router.register(r'types', PropertyTypeViewSet, basename='type')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'', PropertyViewSet, basename='property')

urlpatterns = [
    path('', include(router.urls)),
]
