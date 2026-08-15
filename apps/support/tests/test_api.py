from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.support.models import SupportCategory

class SupportAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='supportuser@dekouway.sn', password='Password123!', is_client=True)
        self.category = SupportCategory.objects.create(name='Technique', slug='technique-api-test')

    def test_create_ticket_add_message_and_close_api(self):
        self.client.force_authenticate(user=self.user)
        create_res = self.client.post('/api/v1/support/tickets/', {
            'category_id': str(self.category.id),
            'subject': 'Problème de connexion WiFi',
            'description': 'Je ne parviens pas à me connecter au réseau WiFi du logement.'
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        ticket_id = create_res.data['id']

        msg_res = self.client.post(f'/api/v1/support/tickets/{ticket_id}/messages/', {
            'content': 'Précision sur la panne : la box clignote rouge.'
        })
        self.assertEqual(msg_res.status_code, status.HTTP_201_CREATED)

        close_res = self.client.post(f'/api/v1/support/tickets/{ticket_id}/close/')
        self.assertEqual(close_res.status_code, status.HTTP_200_OK)

    def test_categories_list_api(self):
        response = self.client.get('/api/v1/support/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
