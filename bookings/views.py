from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import datetime
from properties.models import Property
from .models import Booking

class BookingCreateView(LoginRequiredMixin, View):
    """
    Handles request submission for a booking.
    """
    def post(self, request, property_id):
        # Only allow client accounts to book listings
        if request.user.role != 'client':
            messages.error(request, "Seuls les clients peuvent effectuer des réservations.")
            return redirect('property_detail', pk=property_id)

        property_obj = get_object_or_404(Property, id=property_id, status='approved')
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Veuillez fournir des dates d'arrivée et de départ valides.")
            return redirect('property_detail', pk=property_id)

        booking = Booking(
            property=property_obj,
            client=request.user,
            check_in=check_in,
            check_out=check_out
        )

        try:
            booking.full_clean()
            booking.save()
            messages.success(request, "Votre demande de réservation a été envoyée au propriétaire pour validation !")
            return redirect('bookings_list')
        except Exception as e:
            # Catch ValidationError from clean/save
            error_msg = str(e)
            if hasattr(e, 'message_dict'):
                error_msg = "; ".join([", ".join(v) for v in e.message_dict.values()])
            elif hasattr(e, 'messages'):
                error_msg = "; ".join(e.messages)
            messages.error(request, f"Impossible de réserver : {error_msg}")
            return redirect('property_detail', pk=property_id)


class BookingsListView(LoginRequiredMixin, ListView):
    """
    Displays list of bookings relevant to the current user's role.
    """
    model = Booking
    template_name = 'pages/client/reservations.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return Booking.objects.filter(client=user).select_related('property', 'property__owner')
        elif user.role == 'owner':
            return Booking.objects.filter(property__owner=user).select_related('property', 'client')
        # Admins see everything
        return Booking.objects.all().select_related('property', 'client', 'property__owner')


class BookingActionView(LoginRequiredMixin, View):
    """
    Enables owners or clients to alter booking states (Accept, Reject, Cancel).
    """
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        action = request.POST.get('action')
        user = request.user

        # Validation rules per role
        if user.role == 'owner' and booking.property.owner == user:
            if action == 'approve' and booking.status == 'pending':
                booking.status = 'approved'
                booking.save()
                messages.success(request, "Réservation acceptée ! Le client a été notifié pour procéder au paiement.")
            elif action == 'reject' and booking.status == 'pending':
                booking.status = 'rejected'
                booking.save()
                messages.warning(request, "Réservation rejetée.")
            else:
                messages.error(request, "Action non autorisée ou état invalide.")
        
        elif user.role == 'client' and booking.client == user:
            if action == 'cancel' and booking.status in ['pending', 'approved']:
                booking.status = 'cancelled'
                booking.save()
                messages.success(request, "Votre réservation a été annulée.")
            else:
                messages.error(request, "Impossible d'annuler cette réservation dans son état actuel.")
        
        elif user.role == 'admin' or user.is_superuser:
            # Admin override action
            if action in ['approve', 'reject', 'cancel']:
                if action == 'approve':
                    booking.status = 'approved'
                elif action == 'reject':
                    booking.status = 'rejected'
                elif action == 'cancel':
                    booking.status = 'cancelled'
                booking.save()
                messages.success(request, f"Réservation mise à jour avec le statut {booking.get_status_display()}.")
        else:
            messages.error(request, "Accès refusé.")

        # Redirect back to caller (dashboard or bookings list)
        next_url = request.POST.get('next') or 'bookings_list'
        return redirect(next_url)
