from django.test import SimpleTestCase
from apps.support.forms import SupportTicketForm

class SupportFormsTestCase(SimpleTestCase):
    def test_support_ticket_valid(self):
        form = SupportTicketForm(data={
            'subject': 'Problème de paiement Wave',
            'category_id': 'cat_1',
            'priority': 'HIGH',
            'description': 'Je n\'ai pas reçu la confirmation par SMS suite au paiement effectué sur la plateforme.'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['subject'], 'Problème de paiement Wave')

    def test_support_ticket_subject_too_short(self):
        form = SupportTicketForm(data={
            'subject': 'Aide',
            'category_id': 'cat_1',
            'priority': 'MEDIUM',
            'description': 'Explication suffisamment détaillée du problème rencontré sur la plateforme DEKOUWAY.'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

    def test_support_ticket_description_too_short(self):
        form = SupportTicketForm(data={
            'subject': 'Problème de réservation',
            'category_id': 'cat_1',
            'priority': 'MEDIUM',
            'description': 'Problème'  # Description < 15 chars
        })
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)
