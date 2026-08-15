from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.documents.api.viewsets import DocumentCategoryViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'categories', DocumentCategoryViewSet, basename='document-category')
router.register(r'', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
