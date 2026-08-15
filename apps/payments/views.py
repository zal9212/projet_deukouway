import uuid as uuid_lib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from apps.payments.choices import PaymentMethodChoices
from apps.reservations.choices import ReservationStatusChoices
from apps.reservations.services.exceptions import InvalidWorkflowTransition
from apps.reservations.services.selectors import ReservationSelector
from apps.reservations.services.services import ReservationService
from apps.payments.services.selectors import PaymentSelector
from apps.payments.services.services import PaymentService
from apps.properties.services.services import PropertyService


def _compute_rental_subtotal(req):
    return PropertyService.calculate_price_for_stay(req.property, req.check_in, req.check_out)


class PaymentCheckoutView(LoginRequiredMixin, View):
    """Panneau de règlement pour une demande acceptée par le propriétaire."""

    def get(self, request, booking_id):
        req = ReservationSelector.get_request_by_id(booking_id)
        if not req or req.client_id != request.user.id:
            messages.error(request, "Demande de réservation introuvable.")
            return redirect('bookings_list')

        if req.status != ReservationStatusChoices.PAYMENT_PENDING:
            messages.error(request, "Cette réservation n'est pas encore prête pour le paiement.")
            return redirect('bookings_list')

        rental_subtotal = _compute_rental_subtotal(req)
        service_fee = PaymentSelector.get_platform_settings().client_service_fee
        context = {
            'booking': req,
            'price_per_night': req.property.price,
            'rental_subtotal': rental_subtotal,
            'service_fee': service_fee,
            'total_price': rental_subtotal + service_fee,
        }
        return render(request, 'pages/client/payment.html', context)


class PaymentProcessView(LoginRequiredMixin, View):
    """Traite le règlement simulé et confirme la réservation."""

    def post(self, request, booking_id):
        req = ReservationSelector.get_request_by_id(booking_id)
        if not req or req.client_id != request.user.id:
            messages.error(request, "Demande de réservation introuvable.")
            return redirect('bookings_list')

        if req.status != ReservationStatusChoices.PAYMENT_PENDING:
            messages.error(request, "Statut de réservation invalide pour le paiement.")
            return redirect('bookings_list')

        payment_method = request.POST.get('payment_method')
        if payment_method not in PaymentMethodChoices.values:
            messages.error(request, "Veuillez choisir un moyen de paiement valide.")
            return redirect('payment_checkout', booking_id=req.id)

        rental_subtotal = _compute_rental_subtotal(req)
        service_fee = PaymentSelector.get_platform_settings().client_service_fee
        amount_charged = rental_subtotal + service_fee

        try:
            reservation = ReservationService.confirm_payment(req, rental_subtotal)
        except InvalidWorkflowTransition as exc:
            messages.error(request, str(exc))
            return redirect('bookings_list')

        payment = PaymentService.create_payment(reservation, request.user, amount_charged, payment_method)
        PaymentService.verify_payment(payment, gateway_transaction_id=str(uuid_lib.uuid4()))
        PaymentService.create_commission(payment)

        messages.success(
            request,
            f"Paiement de {amount_charged} FCFA reçu avec succès ! Votre réservation est confirmée."
        )
        return redirect('payment_receipt', booking_id=reservation.id)


class PaymentReceiptView(LoginRequiredMixin, View):
    """Affiche le reçu imprimable d'une réservation payée."""

    def get(self, request, booking_id):
        reservation = ReservationSelector.get_reservation_by_id(booking_id)
        if not reservation:
            messages.error(request, "Réservation introuvable.")
            return redirect('bookings_list')

        user = request.user
        if user.id != reservation.client_id and user.id != reservation.property.owner_id and not user.is_superuser:
            messages.error(request, "Accès non autorisé au reçu.")
            return redirect('public:home')

        payment = reservation.payments.order_by('-created_at').first()
        if not payment:
            messages.error(request, "Aucun paiement enregistré pour cette réservation.")
            return redirect('bookings_list')

        context = {
            'booking': reservation,
            'payment': payment,
            'days': (reservation.check_out - reservation.check_in).days,
        }
        return render(request, 'pages/client/receipt.html', context)
