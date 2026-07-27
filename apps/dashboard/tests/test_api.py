from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User

class DashboardAPITestCase(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email='client@dekouway.sn', password='Password123!', is_client=True)
        self.owner_user = User.objects.create_user(email='owner@dekouway.sn', password='Password123!', is_owner=True)
        self.admin_user = User.objects.create_user(email='admin@dekouway.sn', password='Password123!', is_superadmin=True)

    def test_client_stats_api(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/v1/dashboard/client-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reservations', response.data)

    def test_owner_stats_api(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get('/api/v1/dashboard/owner-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_properties', response.data)

    def test_admin_stats_api(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/dashboard/admin-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
