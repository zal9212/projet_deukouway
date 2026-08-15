from django.test import TestCase, Client
from django.urls import reverse
from apps.support.models import ContactMessage


class ContactFormTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('public:contact')

    def test_contact_form_valid_submission_creates_message(self):
        response = self.client.post(self.url, {
            'name': 'Awa Ndiaye',
            'email': 'awa@test.com',
            'subject': 'Question test',
            'message': 'Ceci est un message de test.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(email='awa@test.com').exists())

    def test_contact_form_missing_fields_rejected(self):
        self.client.post(self.url, {
            'name': '', 'email': '', 'subject': '', 'message': '',
        })
        self.assertEqual(ContactMessage.objects.count(), 0)
