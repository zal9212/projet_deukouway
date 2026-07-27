import re
import logging
import calendar
from datetime import date as date_cls, timedelta
from urllib.parse import urlparse

import requests
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, UpdateView, View
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import Http404, JsonResponse
from django.db import transaction

from apps.core.mixins import OwnerRequiredMixin, ViewExceptionHandlingMixin
from apps.properties.services.selectors import PropertySelector
from apps.reservations.services.selectors import ReservationSelector, ACTIVE_RESERVATION_STATUSES
from apps.reservations.models import Reservation, ReservationRequest
from apps.reservations.choices import ReservationStatusChoices
from apps.payments.services.selectors import PaymentSelector
from apps.documents.services.selectors import DocumentSelector
from apps.support.services.selectors import TicketSelector
from apps.accounts.services.selectors import UserSelector
from apps.dashboard.services.selectors import DashboardSelector
from apps.notifications.services.selectors import NotificationSelector

from apps.properties.services.services import PropertyService
from apps.properties.services.exceptions import DatesAlreadyBooked, UnauthorizedPropertyAction, InvalidPropertyStatus
from apps.reservations.services.services import ReservationService
from apps.accounts.services.services import AccountService
from apps.accounts.services.exceptions import UserAlreadyExists
from apps.documents.services.services import DocumentService
from apps.support.services.services import SupportService
from apps.notifications.services.services import NotificationService

logger = logging.getLogger(__name__)

ALLOWED_MAP_HOSTS = {'maps.google.com', 'google.com', 'goo.gl', 'maps.app.goo.gl'}
COORDINATE_PATTERNS = [
    re.compile(r'@(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)'),
    re.compile(r'!3d(-?\d{1,2}\.\d+)!4d(-?\d{1,3}\.\d+)'),
    re.compile(r'[?&]q=(-?\d{1,2}\.\d+),\+?(-?\d{1,3}\.\d+)'),
    re.compile(r'/maps/search/(-?\d{1,2}\.\d+),\+?(-?\d{1,3}\.\d+)'),
    re.compile(r'^\s*(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)\s*$'),
    re.compile(r'(-?\d{1,2}\.\d{4,}),\+?\s*(-?\d{1,3}\.\d{4,})'),
]


def _extract_coordinates(text):
    """Tente d'extraire une paire (lat, lng) valide depuis un texte/URL Google Maps."""
    for pattern in COORDINATE_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                lat, lng = float(match.group(1)), float(match.group(2))
            except ValueError:
                continue
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return lat, lng
    return None


class ResolveMapLinkView(OwnerRequiredMixin, View):
    """
    Extrait des coordonnées GPS depuis un texte collé par le propriétaire :
    coordonnées brutes, URL Google Maps classique, ou lien court (maps.app.goo.gl)
    qu'il faut suivre via une requête HTTP.

    Seuls les hôtes Google Maps sont autorisés en sortie (whitelist stricte sur le
    netloc réel de l'URL, résistante au spoofing) pour éviter tout risque de SSRF :
    ce endpoint ne doit jamais pouvoir être détourné pour sonder un hôte arbitraire.
    """
    def post(self, request, *args, **kwargs):
        text = request.POST.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'Aucun lien ou coordonnée fourni.'}, status=400)

        coords = _extract_coordinates(text)
        if coords:
            return JsonResponse({'lat': coords[0], 'lng': coords[1]})

        parsed = urlparse(text)
        hostname = (parsed.hostname or '').lower()
        if parsed.scheme not in ('http', 'https') or hostname not in ALLOWED_MAP_HOSTS:
            return JsonResponse({'error': "Collez des coordonnées ou un lien Google Maps valide."}, status=400)

        current_url = text
        for _ in range(5):
            try:
                response = requests.head(current_url, allow_redirects=False, timeout=5)
            except requests.RequestException:
                logger.warning(f"Échec de résolution du lien Google Maps pour {request.user.email}")
                break

            location = response.headers.get('Location')
            if not location:
                break
            current_url = location
            coords = _extract_coordinates(current_url)
            if coords:
                return JsonResponse({'lat': coords[0], 'lng': coords[1]})

        return JsonResponse({'error': "Impossible de déterminer la position à partir de ce lien."}, status=422)


COMMON_AMENITIES = [
    'WiFi', 'Climatisation', 'Piscine', 'Parking gratuit', 'Cuisine équipée',
    'Télévision', 'Lave-linge', 'Sécurité 24/7', 'Vue mer', 'Jardin', 'Groupe électrogène',
]

COMMON_RULES = [
    'Non-fumeur', 'Animaux non admis', 'Fêtes et événements interdits', 'Adapté aux enfants',
]

PRIVATE_ROOM_AMENITIES = [
    'Salle de bain privée', 'Salle de bain partagée', 'Entrée indépendante', 'Petit-déjeuner inclus',
]

ENTIRE_HOME_AMENITIES = [
    'Cuisine tout équipée', 'Buanderie', 'Salon privé', 'Terrasse privée',
]

class OwnerDashboardView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner_id = str(self.request.user.id)
        context['stats'] = DashboardSelector.get_owner_stats(owner_id)
        context['my_properties'] = PropertySelector.get_properties_for_owner(owner_id)[:5]
        context['pending_requests'] = ReservationSelector.get_owner_requests(owner_id)[:5]
        context['recent_payouts'] = PaymentSelector.get_owner_payouts(owner_id)[:5]
        return context

class OwnerPropertiesView(OwnerRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/owner/properties.html'
    context_object_name = 'properties'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        return PropertySelector.get_properties_for_owner(str(self.request.user.id), search_query=search_query, status=status_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner_id = str(self.request.user.id)
        context['pending_count'] = PropertySelector.get_properties_for_owner(owner_id, status='pending').count()
        return context

    def post(self, request, *args, **kwargs):
        property_id = request.POST.get('property_id')
        action = request.POST.get('action')
        prop = PropertySelector.get_property_by_id(property_id)
        if not prop:
            raise Http404("Logement non trouvé.")

        if action == 'archive':
            try:
                PropertyService.archive_property(prop, request.user)
                messages.success(request, f"Le logement '{prop.title}' a été archivé.")
            except UnauthorizedPropertyAction as exc:
                messages.error(request, str(exc))

        return redirect('dashboard:owner_properties')

class OwnerAddPropertyView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/property_add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PropertySelector.get_all_categories()
        context['types'] = PropertySelector.get_all_types()
        context['common_amenities'] = COMMON_AMENITIES
        context['common_rules'] = COMMON_RULES
        context['private_room_amenities'] = PRIVATE_ROOM_AMENITIES
        context['entire_home_amenities'] = ENTIRE_HOME_AMENITIES
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_verified:
            messages.warning(request, "Votre compte est en attente de vérification par notre équipe. Vous pourrez publier un logement une fois votre dossier validé.")
            return redirect('dashboard:owner_add_property')

        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        property_type_id = request.POST.get('property_type_id')
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        images = request.FILES.getlist('images')

        if not (title and description and property_type_id and address and city and district):
            messages.error(request, "Veuillez renseigner tous les champs obligatoires avant de soumettre votre logement.")
            return redirect('dashboard:owner_add_property')

        if not images:
            messages.error(request, "Veuillez ajouter au moins une photo de votre logement.")
            return redirect('dashboard:owner_add_property')

        try:
            price = float(request.POST.get('price', 0))
            surface = int(request.POST.get('surface', 0))
            bedrooms = int(request.POST.get('bedrooms', 0))
            bathrooms = int(request.POST.get('bathrooms', 0))
            max_guests = int(request.POST.get('max_guests', 0))
        except (TypeError, ValueError):
            messages.error(request, "Le prix, la surface et les capacités doivent être des nombres valides.")
            return redirect('dashboard:owner_add_property')

        latitude, longitude = None, None
        raw_lat, raw_lng = request.POST.get('latitude', '').strip(), request.POST.get('longitude', '').strip()
        if raw_lat and raw_lng:
            try:
                latitude, longitude = float(raw_lat), float(raw_lng)
            except ValueError:
                latitude, longitude = None, None

        amenities = request.POST.getlist('amenities')
        rules = request.POST.getlist('rules')
        extra_rule = request.POST.get('extra_rule', '').strip()
        if extra_rule:
            rules.append(extra_rule)

        with transaction.atomic():
            prop = PropertyService.create_property(
                owner=request.user,
                property_type_id=property_type_id,
                title=title,
                description=description,
                price=price,
                address=address,
                city=city,
                district=district,
                surface=surface,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                max_guests=max_guests,
                latitude=latitude,
                longitude=longitude
            )
            PropertyService.add_images(prop, images)
            PropertyService.add_amenities(prop, amenities)
            PropertyService.add_rules(prop, rules)
            PropertyService.submit_for_validation(prop, request.user)

        messages.success(request, f"Le logement '{prop.title}' a été envoyé pour validation à notre équipe.")
        return redirect('dashboard:owner_properties')

class OwnerEditPropertyView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/property_add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prop_id = self.kwargs.get('pk') or self.kwargs.get('id')
        prop = PropertySelector.get_property_by_id(str(prop_id))
        if not prop or str(prop.owner.id) != str(self.request.user.id):
            raise Http404("Logement non trouvé.")
        context['property'] = prop
        context['categories'] = PropertySelector.get_all_categories()
        context['types'] = PropertySelector.get_all_types()
        context['common_amenities'] = COMMON_AMENITIES
        context['common_rules'] = COMMON_RULES
        context['private_room_amenities'] = PRIVATE_ROOM_AMENITIES
        context['entire_home_amenities'] = ENTIRE_HOME_AMENITIES
        context['initial_data'] = {
            'title': prop.title,
            'description': prop.description,
            'property_type_id': str(prop.property_type_id),
            'category_slug': prop.property_type.category.slug,
            'address': prop.address,
            'city': prop.city,
            'district': prop.district,
            'latitude': float(prop.latitude) if prop.latitude is not None else None,
            'longitude': float(prop.longitude) if prop.longitude is not None else None,
            'price': float(prop.price),
            'surface': prop.surface,
            'bedrooms': prop.bedrooms,
            'bathrooms': prop.bathrooms,
            'max_guests': prop.max_guests,
            'amenities': [a.name for a in prop.amenities.all()],
            'rules': [r.rule for r in prop.rules.all()],
            'existing_images_count': prop.images.count(),
        }
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_verified:
            messages.warning(request, "Votre compte est en attente de vérification par notre équipe. Vous pourrez modifier votre logement une fois votre dossier validé.")
            return redirect('dashboard:owner_properties')

        prop_id = self.kwargs.get('pk') or self.kwargs.get('id')
        prop = PropertySelector.get_property_by_id(str(prop_id))
        if not prop or str(prop.owner.id) != str(self.request.user.id):
            raise Http404("Logement non trouvé.")

        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        property_type_id = request.POST.get('property_type_id')
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        district = request.POST.get('district', '').strip()
        images = request.FILES.getlist('images')

        if not (title and description and property_type_id and address and city and district):
            messages.error(request, "Veuillez renseigner tous les champs obligatoires.")
            return redirect('dashboard:owner_edit_property', pk=prop.id)

        try:
            price = float(request.POST.get('price', prop.price))
            surface = int(request.POST.get('surface', prop.surface))
            bedrooms = int(request.POST.get('bedrooms', prop.bedrooms))
            bathrooms = int(request.POST.get('bathrooms', prop.bathrooms))
            max_guests = int(request.POST.get('max_guests', prop.max_guests))
        except (TypeError, ValueError):
            messages.error(request, "Le prix, la surface et les capacités doivent être des nombres valides.")
            return redirect('dashboard:owner_edit_property', pk=prop.id)

        latitude, longitude = prop.latitude, prop.longitude
        raw_lat, raw_lng = request.POST.get('latitude', '').strip(), request.POST.get('longitude', '').strip()
        if raw_lat and raw_lng:
            try:
                latitude, longitude = float(raw_lat), float(raw_lng)
            except ValueError:
                pass

        amenities = request.POST.getlist('amenities')
        rules = request.POST.getlist('rules')
        extra_rule = request.POST.get('extra_rule', '').strip()
        if extra_rule:
            rules.append(extra_rule)

        with transaction.atomic():
            PropertyService.update_property(
                prop, request.user,
                property_type_id=property_type_id,
                title=title,
                description=description,
                address=address,
                city=city,
                district=district,
                latitude=latitude,
                longitude=longitude,
                price=price,
                surface=surface,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                max_guests=max_guests,
            )
            PropertyService.set_amenities(prop, amenities)
            PropertyService.set_rules(prop, rules)
            if images:
                PropertyService.add_images(prop, images, cover_index=(0 if not prop.images.exists() else -1))

        messages.success(request, "Les modifications du logement ont été enregistrées.")
        return redirect('dashboard:owner_properties')

PENDING_REQUEST_STATUSES = [
    ReservationStatusChoices.REQUESTED, ReservationStatusChoices.UNDER_REVIEW,
    ReservationStatusChoices.SENT_TO_OWNER, ReservationStatusChoices.OWNER_ACCEPTED,
    ReservationStatusChoices.PAYMENT_PENDING, ReservationStatusChoices.PAID,
]


class OwnerCalendarView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner_properties = PropertySelector.get_properties_for_owner(str(self.request.user.id))
        context['properties'] = owner_properties

        selected_property = None
        property_id = self.request.GET.get('property')
        if property_id:
            selected_property = owner_properties.filter(id=property_id).first()
        if not selected_property:
            selected_property = owner_properties.first()
        context['selected_property'] = selected_property

        today = date_cls.today()
        try:
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month', today.month))
            date_cls(year, month, 1)
        except (ValueError, TypeError):
            year, month = today.year, today.month

        context['year'] = year
        context['month'] = month
        context['first_of_month'] = date_cls(year, month, 1)

        prev_month_date = date_cls(year, month, 1) - timedelta(days=1)
        next_month_date = (date_cls(year, month, 28) + timedelta(days=4)).replace(day=1)
        context['prev_year'], context['prev_month'] = prev_month_date.year, prev_month_date.month
        context['next_year'], context['next_month'] = next_month_date.year, next_month_date.month

        month_dates = list(calendar.Calendar(firstweekday=0).itermonthdates(year, month))
        confirmed_dates, pending_dates, blocked_dates = set(), set(), set()

        if selected_property:
            range_start, range_end = month_dates[0], month_dates[-1]

            for res in Reservation.objects.filter(
                property_id=selected_property.id, status__in=ACTIVE_RESERVATION_STATUSES, is_deleted=False,
                check_in__lte=range_end, check_out__gte=range_start,
            ):
                d = max(res.check_in, range_start)
                while d < res.check_out and d <= range_end:
                    confirmed_dates.add(d)
                    d += timedelta(days=1)

            for req in ReservationRequest.objects.filter(
                property_id=selected_property.id, status__in=PENDING_REQUEST_STATUSES, is_deleted=False,
                check_in__lte=range_end, check_out__gte=range_start,
            ):
                d = max(req.check_in, range_start)
                while d < req.check_out and d <= range_end:
                    pending_dates.add(d)
                    d += timedelta(days=1)

            blocked_dates = PropertySelector.get_blocked_dates(selected_property.id, range_start, range_end)

        weeks, week = [], []
        for d in month_dates:
            status = 'confirmed' if d in confirmed_dates else 'pending' if d in pending_dates else 'blocked' if d in blocked_dates else None
            week.append({'date': d, 'day': d.day, 'is_current_month': d.month == month, 'status': status})
            if len(week) == 7:
                weeks.append(week)
                week = []
        context['weeks'] = weeks
        return context

    def post(self, request, *args, **kwargs):
        property_id = request.POST.get('property_id')
        prop = PropertySelector.get_property_by_id(property_id)
        if not prop:
            raise Http404("Logement non trouvé.")

        year = request.POST.get('year', '')
        month = request.POST.get('month', '')
        redirect_url = f"{reverse('dashboard:owner_calendar')}?property={prop.id}"
        if year and month:
            redirect_url += f"&year={year}&month={month}"

        try:
            start_date = date_cls.fromisoformat(request.POST.get('start_date', ''))
            end_date = date_cls.fromisoformat(request.POST.get('end_date', ''))
        except ValueError:
            messages.error(request, "Veuillez sélectionner des dates valides.")
            return redirect(redirect_url)

        reason = request.POST.get('reason', '').strip()
        try:
            count = PropertyService.block_dates(prop, request.user, start_date, end_date, reason)
            messages.success(request, f"{count} jour(s) bloqué(s) sur le calendrier.")
        except (DatesAlreadyBooked, UnauthorizedPropertyAction, InvalidPropertyStatus) as exc:
            messages.error(request, str(exc))

        return redirect(redirect_url)

class OwnerRequestsView(OwnerRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/owner/requests.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        return ReservationSelector.get_owner_requests(str(self.request.user.id))

class OwnerRequestDetailView(OwnerRequiredMixin, ViewExceptionHandlingMixin, DetailView):
    template_name = 'pages/dashboard/owner/request_detail.html'
    context_object_name = 'reservation_request'

    def get_object(self, queryset=None):
        req_id = self.kwargs.get('pk') or self.kwargs.get('id')
        req_obj = ReservationSelector.get_request_by_id(str(req_id))
        if not req_obj or str(req_obj.property.owner.id) != str(self.request.user.id):
            raise Http404("Demande non trouvée.")
        return req_obj

    def post(self, request, *args, **kwargs):
        req_obj = self.get_object()
        action = request.POST.get('action')

        if action == 'accept':
            ReservationService.owner_accept(req_obj, request.user)
            messages.success(request, "Demande acceptée. Le client va être invité à régler le séjour.")
        elif action == 'reject':
            reason = request.POST.get('reason', '')
            ReservationService.owner_reject(req_obj, request.user, reason)
            messages.success(request, "Demande refusée.")
        else:
            messages.error(request, "Action non reconnue.")

        return redirect('dashboard:owner_request_detail', pk=req_obj.id)

class OwnerPayoutsView(OwnerRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/owner/payouts.html'
    context_object_name = 'payouts'
    paginate_by = 10

    def get_queryset(self):
        return PaymentSelector.get_owner_payouts(str(self.request.user.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_payout_total'] = PaymentSelector.get_owner_pending_payout_total(str(self.request.user.id))
        return context

class OwnerPayoutsExportView(OwnerRequiredMixin, ViewExceptionHandlingMixin, View):
    def get(self, request, *args, **kwargs):
        import csv
        from django.http import HttpResponse

        payouts = PaymentSelector.get_owner_payouts(str(request.user.id))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="versements_dekouway.csv"'
        writer = csv.writer(response)
        writer.writerow(['Réservation', 'Logement', 'Date', 'Méthode', 'Montant', 'Devise', 'Statut'])
        for payout in payouts:
            writer.writerow([
                payout.reservation.confirmation_code or str(payout.reservation.id)[:8],
                payout.reservation.property.title,
                payout.created_at.strftime('%Y-%m-%d'),
                payout.get_method_display(),
                payout.amount,
                payout.currency,
                payout.get_status_display(),
            ])
        return response

class OwnerStatsView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = DashboardSelector.get_owner_stats(str(self.request.user.id))
        context['charts'] = DashboardSelector.get_owner_monthly_charts(str(self.request.user.id))
        return context

class OwnerDocumentsView(OwnerRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/owner/documents.html'
    context_object_name = 'documents'
    paginate_by = 10

    def get_queryset(self):
        return DocumentSelector.get_user_documents(str(self.request.user.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = DocumentSelector.get_all_categories()
        return context

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title', '')
        category_id = request.POST.get('category')
        file_obj = request.FILES.get('file')
        category = DocumentSelector.get_all_categories().filter(id=category_id).first()
        if file_obj and category:
            DocumentService.upload(request.user, category, title or file_obj.name, file_obj)
            messages.success(request, "Document téléchargé avec succès !")
        else:
            messages.error(request, "Veuillez sélectionner une catégorie et un fichier valides.")
        return redirect('dashboard:owner_documents')

class OwnerProfileView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = UserSelector.get_user_profile(str(self.request.user.id))
        return context

    def post(self, request, *args, **kwargs):
        new_email = request.POST.get('email')
        if new_email and new_email != request.user.email:
            try:
                AccountService.change_email(request.user, new_email)
                messages.success(request, "Adresse email mise à jour.")
            except UserAlreadyExists:
                messages.error(request, "Cet email est déjà utilisé par un autre compte.")

        profile = UserSelector.get_user_profile(request.user)
        profile.first_name = request.POST.get('first-name', profile.first_name)
        profile.last_name = request.POST.get('last-name', profile.last_name)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.save(update_fields=['first_name', 'last_name', 'phone'])

        messages.info(request, "Informations de profil enregistrées.")
        return redirect('dashboard:owner_profile')

class OwnerSecurityView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/security.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = UserSelector.get_user_sessions(str(self.request.user.id))
        return context

    def post(self, request, *args, **kwargs):
        current_password = request.POST.get('current_password', '')
        new_pass = request.POST.get('new_password', '')

        if not request.user.check_password(current_password):
            messages.error(request, "Le mot de passe actuel est incorrect.")
        elif len(new_pass) < 8:
            messages.error(request, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
        else:
            AccountService.change_password(request.user, new_pass)
            update_session_auth_hash(request, request.user)
            messages.success(request, "Mot de passe modifié.")
        return redirect('dashboard:owner_security')

class OwnerSettingsView(OwnerRequiredMixin, ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/dashboard/owner/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = UserSelector.get_user_profile(self.request.user)
        context['preferences'] = NotificationSelector.get_or_create_preferences(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        NotificationService.update_preferences(
            request.user,
            email_enabled=bool(request.POST.get('email_enabled')),
            sms_enabled=bool(request.POST.get('sms_enabled')),
        )
        messages.success(request, "Préférences de notification enregistrées.")
        return redirect('dashboard:owner_settings')

class OwnerSupportView(OwnerRequiredMixin, ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/dashboard/owner/help.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        return TicketSelector.get_user_tickets(str(self.request.user.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TicketSelector.get_categories()
        return context

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get('category')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('message', '').strip()
        category = TicketSelector.get_categories().filter(id=category_id).first()
        if category and subject and description:
            SupportService.create_ticket(request.user, category, subject, description)
            messages.success(request, "Votre message a été envoyé au support.")
        else:
            messages.error(request, "Veuillez renseigner un sujet, une catégorie et un message.")
        return redirect('dashboard:owner_support')
