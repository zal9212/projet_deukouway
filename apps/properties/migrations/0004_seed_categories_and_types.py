from django.db import migrations


CATEGORIES = {
    'logement-entier': {
        'name': 'Logement entier',
        'types': [
            ('villa', 'Villa'),
            ('appartement', 'Appartement'),
            ('maison', 'Maison'),
            ('studio', 'Studio'),
            ('duplex', 'Duplex'),
        ],
    },
    'chambre-privee': {
        'name': 'Chambre privée',
        'types': [
            ('chambre-chez-habitant', 'Chambre chez l\'habitant'),
        ],
    },
}


def seed_categories(apps, schema_editor):
    PropertyCategory = apps.get_model('properties', 'PropertyCategory')
    PropertyType = apps.get_model('properties', 'PropertyType')

    for cat_slug, cat_data in CATEGORIES.items():
        category, _ = PropertyCategory.objects.get_or_create(
            slug=cat_slug, defaults={'name': cat_data['name']}
        )
        for type_slug, type_name in cat_data['types']:
            PropertyType.objects.get_or_create(
                slug=type_slug, defaults={'name': type_name, 'category': category}
            )


def remove_categories(apps, schema_editor):
    PropertyCategory = apps.get_model('properties', 'PropertyCategory')
    PropertyType = apps.get_model('properties', 'PropertyType')
    PropertyType.objects.filter(slug__in=[t for c in CATEGORIES.values() for t, _ in c['types']]).delete()
    PropertyCategory.objects.filter(slug__in=CATEGORIES.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0003_propertyreview'),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
