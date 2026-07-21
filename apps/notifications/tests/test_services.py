from django.test import TestCase
from apps.accounts.models import User
from apps.notifications.services.services import NotificationService
from apps.notifications.services.selectors import NotificationSelector

class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="password")

    def test_create_notification(self):
        notif = NotificationService.notify_client(self.user, "Title", "Message")
        self.assertEqual(notif.user, self.user)
        self.assertFalse(notif.is_read)

    def test_mark_as_read(self):
        notif = NotificationService.notify_client(self.user, "Title", "Message")
        NotificationService.mark_as_read(notif)
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_get_unread(self):
        NotificationService.notify_client(self.user, "Title", "Message")
        unread = NotificationSelector.get_unread_notifications(self.user.id)
        self.assertEqual(unread.count(), 1)
