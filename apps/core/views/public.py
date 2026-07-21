from django.views.generic import TemplateView
from apps.properties.services.selectors import PropertySelector

class HomeView(TemplateView):
    template_name = 'pages/public/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Using selector to fetch featured properties (approved, active)
        # In a real app we might want a specific selector for "featured"
        try:
            properties = PropertySelector.get_available_properties()
            context['featured_properties'] = properties[:6]
        except Exception:
            context['featured_properties'] = []
        return context

class FAQView(TemplateView):
    template_name = 'pages/public/faq.html'

class AboutView(TemplateView):
    template_name = 'pages/public/about.html'

class ContactView(TemplateView):
    template_name = 'pages/public/contact.html'

class LegalView(TemplateView):
    template_name = 'pages/public/legal.html'

class PrivacyView(TemplateView):
    template_name = 'pages/public/privacy.html'

class TermsView(TemplateView):
    template_name = 'pages/public/terms.html'
