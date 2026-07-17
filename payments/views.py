from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from bookings.models import Booking
from .models import Payment

class PaymentCheckoutView(LoginRequiredMixin, View):
    """
    Renders checkout review panel with interactive card & mobile gateway simulators.
    """
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, client=request.user)
        
        # Verify booking is approved and eligible for payment
        if booking.status != 'approved':
            messages.error(request, "Cette réservation n'est pas approuvée ou a déjà été réglée.")
            return redirect('bookings_list')

        context = {
            'booking': booking,
            'price_per_night': booking.property.price_per_night,
            'total_price': booking.total_price
        }
        return render(request, 'pages/client/payment.html', context)


class PaymentProcessView(LoginRequiredMixin, View):
    """
    Processes simulated transaction and updates booking state on success.
    """
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, client=request.user)

        if booking.status != 'approved':
            messages.error(request, "Statut de réservation invalide pour le paiement.")
            return redirect('bookings_list')

        payment_method = request.POST.get('payment_method')
        if not payment_method:
            messages.error(request, "Veuillez choisir un moyen de paiement.")
            return redirect('payment_checkout', booking_id=booking.id)

        # Create Payment Record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            payment_method=payment_method,
            status='completed'  # Simulated success
        )

        # Update Booking Status to Confirmed (Paid)
        booking.status = 'confirmed'
        booking.save()

        messages.success(
            request, 
            f"Paiement de {booking.total_price} FCFA reçu avec succès ! Votre réservation est confirmée."
        )
        return redirect('payment_receipt', booking_id=booking.id)


class PaymentReceiptView(LoginRequiredMixin, View):
    """
    Renders printable receipt showing booking and transaction details.
    """
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Ensure only the owner, client, or admin can access the receipt
        if request.user != booking.client and request.user != booking.property.owner and not request.user.is_superuser:
            messages.error(request, "Accès non autorisé au reçu.")
            return redirect('home')

        # Safely retrieve payment record or create a dummy in case of inconsistencies
        payment = getattr(booking, 'payment', None)
        if not payment:
            messages.error(request, "Aucun paiement enregistré pour cette réservation.")
            return redirect('bookings_list')

        context = {
            'booking': booking,
            'payment': payment,
            'days': (booking.check_out - booking.check_in).days
        }
        return render(request, 'pages/client/receipt.html', context)
