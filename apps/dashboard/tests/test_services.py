from django.test import TestCase
from apps.accounts.models import User
from apps.dashboard.services.services import DashboardService

class DashboardServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="password")

    def test_calculate_statistics(self):
        stats = DashboardService.calculate_statistics()
        self.assertEqual(stats["total_users"], 1)

    def test_get_client_dashboard(self):
        dash = DashboardService.get_client_dashboard(self.user)
        self.assertIn("total_bookings", dash)
