from django.views.generic import TemplateView
from properties.models import Property

class HomeView(TemplateView):
    """
    Home page view displaying featured properties.
    """
    template_name = 'pages/public/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Retrieve available properties verified by admin
            context['featured_properties'] = Property.objects.filter(
                status='approved',
                is_available=True
            ).select_related('owner')[:6]
        except Exception:
            context['featured_properties'] = []
        return context
