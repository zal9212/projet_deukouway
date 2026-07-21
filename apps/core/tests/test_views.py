from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User

class PublicViewsTests(TestCase):
    def test_home_page_status_code(self):
        response = self.client.get(reverse('public:home'))
        self.assertEqual(response.status_code, 200)

    def test_faq_page_status_code(self):
        response = self.client.get(reverse('public:faq'))
        self.assertEqual(response.status_code, 200)

class MixinsSecurityTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@test.com", password="pwd", is_client=True)
        self.owner_user = User.objects.create_user(email="owner@test.com", password="pwd", is_owner=True)
        self.admin_user = User.objects.create_superuser(email="admin@test.com", password="pwd")

    def test_client_dashboard_unauthenticated(self):
        response = self.client.get(reverse('dashboard:client_home'))
        self.assertEqual(response.status_code, 302) # Redirects to login

    def test_client_dashboard_authenticated(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('dashboard:client_home'))
        self.assertEqual(response.status_code, 200)
        
    def test_owner_dashboard_authenticated(self):
        # Must be active to be verified owner
        self.owner_user.is_active = True
        self.owner_user.save()
        self.client.force_login(self.owner_user)
        response = self.client.get(reverse('dashboard:owner_home'))
        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_pending(self):
        self.owner_user.is_active = False
        self.owner_user.save()
        self.client.force_login(self.owner_user)
        response = self.client.get(reverse('dashboard:owner_home'))
        self.assertEqual(response.status_code, 302) # Redirects to owner_pending
        self.assertTrue(response.url.startswith(reverse('accounts:owner_pending')))

    def test_admin_dashboard_authenticated(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('dashboard:admin_home'))
        self.assertEqual(response.status_code, 200)
