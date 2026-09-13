from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_alter_platformsettings_commission_percentage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commission',
            options={'verbose_name': 'Commission KYI IMMOBILIER', 'verbose_name_plural': 'Commissions KYI IMMOBILIER'},
        ),
    ]
