from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTestCase(TestCase):
    """
    Test cases for custom User model constraints and role assignments.
    """
    def setUp(self):
        # Create standard client
        self.client_user = User.objects.create_user(
            username='client_test',
            email='client@test.com',
            password='testpassword123',
            first_name='Mamadou',
            last_name='Ndiaye',
            role='client',
            phone='+221770000001'
        )
        
        # Create owner
        self.owner_user = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpassword123',
            first_name='Abdou',
            last_name='Diouf',
            role='owner',
            phone='+221770000002',
            owner_status='pending',
            is_verified_owner=False
        )

    def test_user_creation_roles(self):
        """Verify role fields are assigned correctly."""
        self.assertEqual(self.client_user.role, 'client')
        self.assertEqual(self.owner_user.role, 'owner')
        
    def test_client_status_automatically_approved(self):
        """Clients should not go through moderation approval processes."""
        self.client_user.save()
        self.assertEqual(self.client_user.owner_status, 'approved')
        self.assertFalse(self.client_user.is_verified_owner)

    def test_owner_status_initially_pending(self):
        """Owner status must require validation before activation."""
        self.assertEqual(self.owner_user.owner_status, 'pending')
        self.assertFalse(self.owner_user.is_verified_owner)
