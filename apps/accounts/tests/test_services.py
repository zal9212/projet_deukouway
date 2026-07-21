from django.test import TestCase
from apps.accounts.models import User, UserProfile
from apps.accounts.services.services import AccountService
from apps.accounts.services.exceptions import UserAlreadyExists, InvalidRoleException

class AccountServiceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@dekouway.com", password="password")

    def test_register_client_success(self):
        user = AccountService.register_client("client@test.com", "password", "John", "Doe")
        self.assertTrue(user.is_client)
        self.assertFalse(user.is_owner)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_register_client_duplicate_email(self):
        AccountService.register_client("client@test.com", "password", "John", "Doe")
        with self.assertRaises(UserAlreadyExists):
            AccountService.register_client("client@test.com", "password", "Jane", "Doe")

    def test_register_owner_success(self):
        user = AccountService.register_owner("owner@test.com", "password", "Jane", "Doe")
        self.assertFalse(user.is_client)
        self.assertTrue(user.is_owner)
        self.assertFalse(user.is_active)  # Pending approval

    def test_approve_owner_success(self):
        user = AccountService.register_owner("owner@test.com", "password", "Jane", "Doe")
        approved_user = AccountService.approve_owner(user, self.admin)
        self.assertTrue(approved_user.is_active)

    def test_approve_client_as_owner_fails(self):
        user = AccountService.register_client("client@test.com", "password", "John", "Doe")
        with self.assertRaises(InvalidRoleException):
            AccountService.approve_owner(user, self.admin)

    def test_block_user(self):
        user = AccountService.register_client("client@test.com", "password", "John", "Doe")
        blocked_user = AccountService.block_user(user, self.admin)
        self.assertFalse(blocked_user.is_active)
