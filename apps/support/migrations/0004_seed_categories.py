from django.db import migrations


CATEGORIES = [
    ('technique', 'Problème technique', "Bug, page qui ne fonctionne pas, erreur d'affichage."),
    ('facturation', 'Facturation & Paiements', 'Question sur un paiement, un versement ou une facture.'),
    ('reservation', 'Réservation', 'Question sur une demande ou une réservation en cours.'),
    ('compte', 'Compte & Vérification', "Vérification d'identité, accès au compte, informations personnelles."),
    ('logement', 'Logement / Annonce', "Question sur la publication ou la gestion d'un logement."),
    ('autre', 'Autre', 'Toute autre demande.'),
]


def seed_categories(apps, schema_editor):
    SupportCategory = apps.get_model('support', 'SupportCategory')
    for slug, name, description in CATEGORIES:
        SupportCategory.objects.get_or_create(slug=slug, defaults={'name': name, 'description': description})


def remove_categories(apps, schema_editor):
    SupportCategory = apps.get_model('support', 'SupportCategory')
    SupportCategory.objects.filter(slug__in=[slug for slug, _, _ in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_alter_complaint_status_alter_ticket_status_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
