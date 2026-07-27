from django.urls import path
from .views.public import (
    HomeView, SearchView, SearchResultsView, PropertyDetailView, ToggleFavoriteView,
    FAQView, OwnerFAQView, AboutView, ContactView, LegalView, PrivacyView, TermsView
)

app_name = 'public'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('recherche/', SearchView.as_view(), name='search'),
    path('recherche/', SearchView.as_view(), name='properties_list'),
    path('recherche/resultats/', SearchResultsView.as_view(), name='search_results'),
    path('logement/<uuid:pk>/', PropertyDetailView.as_view(), name='property_detail'),
    path('logement/<uuid:pk>/favori/', ToggleFavoriteView.as_view(), name='favorite_toggle'),
    path('faq/', FAQView.as_view(), name='faq'),
    path('faq-hote/', OwnerFAQView.as_view(), name='faq_owner'),
    path('a-propos/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('mentions-legales/', LegalView.as_view(), name='legal'),
    path('politique-confidentialite/', PrivacyView.as_view(), name='privacy'),
    path('conditions-generales/', TermsView.as_view(), name='terms'),
]
