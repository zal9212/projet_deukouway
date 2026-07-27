from django.db import migrations


CATEGORIES = [
    ('piece-identite', "Pièce d'identité"),
    ('justificatif-domicile', 'Justificatif de domicile'),
    ('contrat-mandat', 'Contrat de mandat'),
    ('facture-commission', 'Facture de commission'),
    ('document-fiscal', 'Document fiscal'),
    ('autre', 'Autre'),
]


def seed_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    for slug, name in CATEGORIES:
        DocumentCategory.objects.get_or_create(slug=slug, defaults={'name': name})


def remove_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('documents', 'DocumentCategory')
    DocumentCategory.objects.filter(slug__in=[slug for slug, _ in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_alter_document_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
