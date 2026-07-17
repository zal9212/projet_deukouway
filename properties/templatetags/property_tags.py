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
    Rotation circulaire sur les 6 images disponibles.
    """
    index = (int(property_id) - 1) % len(PLACEHOLDER_IMAGES)
    return static(PLACEHOLDER_IMAGES[index])
