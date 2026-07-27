from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView

from apps.properties.choices import PropertyStatusChoices
from apps.properties.services.selectors import PropertySelector
from apps.reservations.forms import ReservationRequestForm
from apps.reservations.services.exceptions import InvalidWorkflowTransition, DatesNotAvailable
from apps.reservations.services.selectors import ReservationSelector
from apps.reservations.services.services import ReservationService


class BookingCreateView(LoginRequiredMixin, View):
    """Soumet une demande de réservation pour un logement publié."""

    def post(self, request, property_id):
        if not getattr(request.user, 'is_client', False):
            messages.error(request, "Seuls les voyageurs peuvent effectuer des réservations.")
            return redirect('public:property_detail', pk=property_id)

        property_obj = PropertySelector.get_property_by_id(property_id)
        if not property_obj or property_obj.status != PropertyStatusChoices.PUBLISHED:
            messages.error(request, "Ce logement n'est pas disponible à la réservation.")
            return redirect('public:property_detail', pk=property_id)

        form = ReservationRequestForm(request.POST)
        if not form.is_valid():
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
            return redirect('public:property_detail', pk=property_id)

        try:
            ReservationService.create_request(
                client=request.user,
                prop=property_obj,
                check_in=form.cleaned_data['check_in'],
                check_out=form.cleaned_data['check_out'],
                guests=form.cleaned_data['guests'],
                special_requests=form.cleaned_data['special_requests'],
            )
            messages.success(
                request,
                "Votre demande de réservation a été envoyée ! Elle sera examinée par DEKOUWAY avant transmission à l'hôte."
            )
        except (DatesNotAvailable, InvalidWorkflowTransition) as exc:
            messages.error(request, str(exc))
            return redirect('public:property_detail', pk=property_id)

        return redirect('bookings_list')


class BookingsListView(LoginRequiredMixin, ListView):
    """Affiche les demandes en cours et les réservations confirmées du client."""
    template_name = 'pages/client/reservations.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return ReservationSelector.get_client_requests(str(self.request.user.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = ReservationSelector.get_client_reservations(str(self.request.user.id))
        return context


class BookingActionView(LoginRequiredMixin, View):
    """Permet au client d'annuler sa propre demande de réservation."""

    def post(self, request, booking_id):
        action = request.POST.get('action')
        req = ReservationSelector.get_request_by_id(booking_id)

        if not req or req.client_id != request.user.id:
            messages.error(request, "Demande de réservation introuvable.")
            return redirect('bookings_list')

        if action == 'cancel':
            try:
                ReservationService.cancel_request(req, request.user)
                messages.success(request, "Votre demande de réservation a été annulée.")
            except InvalidWorkflowTransition as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Action non autorisée.")

        return redirect('bookings_list')
