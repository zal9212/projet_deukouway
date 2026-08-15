from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User

class AIAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@dekouway.sn', password='Password123!', is_client=True)

    def test_chat_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/ai/chat/', {
            'message': 'Bonjour, quelles sont les démarches pour annuler une réservation ?'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reply', response.data)

    def test_recommendations_api(self):
        response = self.client.post('/api/v1/ai/recommendations/', {
            'city': 'Dakar',
            'max_price': '150000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('has_direct_matches', response.data)

    def test_moderation_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/ai/moderation/', {
            'text': 'Mon numéro personnel est 770000000'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['flagged'])

    def test_summary_api(self):
        response = self.client.post('/api/v1/ai/summary/', {
            'title': 'Appartement Fann',
            'description': 'Superbe appartement proche du centre-ville et des universités.'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)

    def test_description_gen_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/ai/description/', {
            'title': 'Studio Mermoz',
            'property_type': 'Studio',
            'city': 'Dakar',
            'district': 'Mermoz',
            'price': '50000.00',
            'surface': 50,
            'bedrooms': 1,
            'bathrooms': 1
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('generated_description', response.data)

    def test_conversation_history_api(self):
        self.client.force_authenticate(user=self.user)
        list_res = self.client.get('/api/v1/ai/history/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)

        clear_res = self.client.delete('/api/v1/ai/history/clear/')
        self.assertEqual(clear_res.status_code, status.HTTP_204_NO_CONTENT)
