from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<uuid:booking_id>/', views.PaymentCheckoutView.as_view(), name='payment_checkout'),
    path('process/<uuid:booking_id>/', views.PaymentProcessView.as_view(), name='payment_process'),
    path('receipt/<uuid:booking_id>/', views.PaymentReceiptView.as_view(), name='payment_receipt'),
]
