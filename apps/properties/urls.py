from django.urls import path
from .views.public import PropertySearchView, PropertyDetailView

app_name = 'properties'

urlpatterns = [
    path('recherche/', PropertySearchView.as_view(), name='search'),
    path('<uuid:pk>/', PropertyDetailView.as_view(), name='detail'),
]
