from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookingsListView.as_view(), name='bookings_list'),
    path('create/<uuid:property_id>/', views.BookingCreateView.as_view(), name='booking_create'),
    path('action/<uuid:booking_id>/', views.BookingActionView.as_view(), name='booking_action'),
]
