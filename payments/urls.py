from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:booking_id>/', views.PaymentCheckoutView.as_view(), name='payment_checkout'),
    path('process/<int:booking_id>/', views.PaymentProcessView.as_view(), name='payment_process'),
    path('receipt/<int:booking_id>/', views.PaymentReceiptView.as_view(), name='payment_receipt'),
]
