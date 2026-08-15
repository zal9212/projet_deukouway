import hashlib

from django import template
from django.templatetags.static import static

register = template.Library()

# 6 images locales disponibles dans static/img/
PLACEHOLDER_IMAGES = [
    'img/property_1.png',
    'img/property_2.png',
    'img/property_3.png',
    'img/property_4.png',
    'img/property_5.png',
    'img/property_6.png',
]


@register.simple_tag
def placeholder_image(property_id):
    """
    Retourne l'URL statique complète d'une image fictive basée sur l'ID du bien.
    Rotation circulaire sur les 6 images disponibles. Les ID étant des UUID (non
    convertibles en int), on dérive un index stable via un hash MD5.
    """
    digest = hashlib.md5(str(property_id).encode()).hexdigest()
    index = int(digest, 16) % len(PLACEHOLDER_IMAGES)
    return static(PLACEHOLDER_IMAGES[index])


@register.filter
def price_unit(pricing_period):
    """Libellé affiché après le prix : '/ nuit' ou '/ mois' selon le type de location."""
    return '/ mois' if pricing_period == 'MONTHLY' else '/ nuit'
