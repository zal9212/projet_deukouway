from django.urls import path
from .views.public import HomeView, FAQView, AboutView, ContactView, LegalView, PrivacyView, TermsView

app_name = 'public'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('faq/', FAQView.as_view(), name='faq'),
    path('a-propos/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('mentions-legales/', LegalView.as_view(), name='legal'),
    path('politique-confidentialite/', PrivacyView.as_view(), name='privacy'),
    path('conditions-generales/', TermsView.as_view(), name='terms'),
]
