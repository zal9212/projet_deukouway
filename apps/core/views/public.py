from django.db.models import Avg, Count
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, View
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import ViewExceptionHandlingMixin
from apps.properties.models import PropertyReview, PropertyFavorite
from apps.properties.services.selectors import PropertySelector
from apps.support.services.selectors import TicketSelector
from apps.support.services.services import SupportService

class HomeView(ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/public/home.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        # Déjà triées par -created_at (plus récentes en premier) dans le selector.
        return PropertySelector.get_published_properties()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Carrousel horizontal mobile ("Logements recommandés") : sélection courte
        # distincte de la grille paginée desktop, pas de pagination sur un scroller.
        context['featured_properties'] = PropertySelector.get_featured_properties(limit=6)
        context['categories'] = PropertySelector.get_all_categories()
        context['user_favorite_ids'] = PropertySelector.get_user_favorite_ids(
            self.request.user.id if self.request.user.is_authenticated else None
        )
        return context

class SearchView(ViewExceptionHandlingMixin, ListView):
    template_name = 'pages/public/search.html'
    context_object_name = 'properties'
    paginate_by = 9

    def get_queryset(self):
        query = self.request.GET.get('search') or self.request.GET.get('q')
        city = self.request.GET.get('city')
        district = self.request.GET.get('neighborhood') or self.request.GET.get('district')
        min_price = self.request.GET.get('price_min') or self.request.GET.get('min_price')
        max_price = self.request.GET.get('price_max') or self.request.GET.get('max_price')
        property_type = self.request.GET.get('type')
        sort_by = self.request.GET.get('sort') or self.request.GET.get('sort_by')
        bedrooms = self.request.GET.get('bedrooms')
        bathrooms = self.request.GET.get('bathrooms')

        amenities = [
            name for flag, name in (
                ('wifi', 'WiFi'), ('climatisation', 'Climatisation'),
                ('parking', 'Parking'), ('piscine', 'Piscine'),
                ('vue_mer', 'Vue mer'),
            ) if self.request.GET.get(flag)
        ]

        def _to_float(value):
            try:
                return float(value) if value else None
            except ValueError:
                return None

        def _to_int(value):
            try:
                return int(value) if value else None
            except ValueError:
                return None

        return PropertySelector.search_properties(
            query=query,
            city=city,
            district=district,
            min_price=_to_float(min_price),
            max_price=_to_float(max_price),
            property_type=property_type,
            sort_by=sort_by,
            min_bedrooms=_to_int(bedrooms),
            min_bathrooms=_to_int(bathrooms),
            amenities=amenities,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PropertySelector.get_all_categories()
        context['types'] = PropertySelector.get_all_types()
        context['user_favorite_ids'] = PropertySelector.get_user_favorite_ids(
            self.request.user.id if self.request.user.is_authenticated else None
        )
        return context

class SearchResultsView(SearchView):
    """Vue dédiée au rendu des résultats de recherche filtrés."""
    template_name = 'pages/public/search.html'

class PropertyDetailView(ViewExceptionHandlingMixin, DetailView):
    template_name = 'pages/public/property_detail.html'
    context_object_name = 'property'

    def get_object(self, queryset=None):
        property_id = self.kwargs.get('pk') or self.kwargs.get('id')
        prop = PropertySelector.get_property_by_id(property_id)
        if not prop:
            raise Http404("Logement non trouvé.")
        return prop

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prop = self.object

        reviews = prop.reviews.select_related('user__profile').order_by('-created_at')
        review_stats = reviews.aggregate(avg=Avg('rating'), count=Count('id'))
        context['reviews'] = reviews[:10]
        context['review_count'] = review_stats['count'] or 0
        context['avg_rating'] = round(review_stats['avg'], 2) if review_stats['avg'] else None

        context['amenities'] = prop.amenities.all()
        context['rules'] = prop.rules.all()

        owner_reviews = PropertyReview.objects.filter(property__owner_id=prop.owner_id)
        owner_review_stats = owner_reviews.aggregate(avg=Avg('rating'), count=Count('id'))
        context['owner_review_count'] = owner_review_stats['count'] or 0
        context['owner_avg_rating'] = round(owner_review_stats['avg'], 2) if owner_review_stats['avg'] else None
        context['owner_properties_count'] = prop.owner.properties.filter(is_deleted=False).count()

        context['today'] = timezone.now().date()
        context['is_favorite'] = (
            self.request.user.is_authenticated
            and PropertyFavorite.objects.filter(user=self.request.user, property_id=prop.id).exists()
        )
        context['similar_properties'] = PropertySelector.get_similar_properties(prop, limit=4)
        context['user_favorite_ids'] = PropertySelector.get_user_favorite_ids(
            self.request.user.id if self.request.user.is_authenticated else None
        )
        return context

class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        prop = PropertySelector.get_property_by_id(pk)
        if not prop:
            raise Http404("Logement non trouvé.")

        favorite = PropertyFavorite.objects.filter(user=request.user, property_id=prop.id).first()
        if favorite:
            favorite.delete()
            messages.info(request, "Logement retiré de vos favoris.")
        else:
            PropertyFavorite.objects.create(user=request.user, property_id=prop.id)
            messages.success(request, "Logement ajouté à vos favoris.")

        if request.headers.get('HX-Request') == 'true':
            # Le bouton se met à jour côté client (Alpine) ; pas de contenu à renvoyer.
            return HttpResponse(status=204)
        return redirect(request.META.get('HTTP_REFERER') or 'public:property_detail', pk=prop.id)

class FAQView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['support_categories'] = TicketSelector.get_categories()
        return context

class OwnerFAQView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/faq_owner.html'

class AboutView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/about.html'

class ContactView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/contact.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not (name and email and subject and message):
            messages.error(request, "Merci de renseigner tous les champs du formulaire.")
            return redirect('public:contact')

        SupportService.submit_contact_message(name, email, subject, message, user=request.user)
        messages.success(
            request,
            "Votre message a bien été envoyé. Notre équipe vous répondra sous 24 à 48h ouvrées."
        )
        return redirect('public:contact')

class LegalView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/legal.html'

class PrivacyView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/privacy.html'

class TermsView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/public/terms.html'
