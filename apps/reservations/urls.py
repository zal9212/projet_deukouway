from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookingsListView.as_view(), name='bookings_list'),
    path('create/<int:property_id>/', views.BookingCreateView.as_view(), name='booking_create'),
    path('action/<int:booking_id>/', views.BookingActionView.as_view(), name='booking_action'),
]
