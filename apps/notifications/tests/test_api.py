from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.notifications.models import Notification

class NotificationsAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@dekouway.sn', password='Password123!', is_client=True)
        self.notif = Notification.objects.create(
            user=self.user,
            title='Bienvenue sur DEKOUWAY',
            message='Votre inscription a été validée.'
        )

    def test_list_notifications_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_as_read_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/notifications/{self.notif.id}/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])

    def test_mark_all_read_and_unread_count_api(self):
        self.client.force_authenticate(user=self.user)
        count_res = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(count_res.status_code, status.HTTP_200_OK)

        all_read_res = self.client.post('/api/v1/notifications/mark-all-read/')
        self.assertEqual(all_read_res.status_code, status.HTTP_200_OK)

    def test_notification_preferences_api(self):
        self.client.force_authenticate(user=self.user)
        get_res = self.client.get('/api/v1/notifications/preferences/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)

        update_res = self.client.put('/api/v1/notifications/preferences/', {
            'email_enabled': False,
            'push_enabled': True
        })
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertFalse(update_res.data['email_enabled'])
