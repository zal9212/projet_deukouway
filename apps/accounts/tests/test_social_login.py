from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from allauth.socialaccount.models import SocialAccount, SocialLogin

from apps.accounts.adapters import SocialAccountAdapter, AccountAdapter
from apps.accounts.models import User, UserProfile
from apps.accounts.services.services import AccountService


def _build_sociallogin(email, first_name, last_name, uid='google-uid-123'):
    user = User(email=email, first_name=first_name, last_name=last_name)
    account = SocialAccount(provider='google', uid=uid, extra_data={
        'email': email, 'given_name': first_name, 'family_name': last_name,
    })
    return SocialLogin(user=user, account=account)


class SocialAccountAdapterTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/accounts/google/login/callback/')
        SessionMiddleware(lambda r: None).process_request(self.request)
        self.request.session.save()
        MessageMiddleware(lambda r: None).process_request(self.request)
        self.adapter = SocialAccountAdapter()

    def test_new_google_signup_creates_client_with_profile(self):
        sociallogin = _build_sociallogin('nouveau@dekouway.sn', 'Awa', 'Diop')

        user = self.adapter.save_user(self.request, sociallogin)

        user.refresh_from_db()
        self.assertTrue(user.is_client)
        self.assertFalse(user.is_owner)
        self.assertTrue(user.email_verified)
        self.assertFalse(user.has_usable_password())

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.first_name, 'Awa')
        self.assertEqual(profile.last_name, 'Diop')

        self.assertTrue(SocialAccount.objects.filter(user=user, provider='google').exists())

    def test_is_open_for_signup_allows_social_but_blocks_plain_account_signup(self):
        sociallogin = _build_sociallogin('autre@dekouway.sn', 'Moussa', 'Fall')
        self.assertTrue(self.adapter.is_open_for_signup(self.request, sociallogin))
        self.assertFalse(AccountAdapter().is_open_for_signup(self.request))

    def test_does_not_duplicate_profile_if_already_linked(self):
        # Simule un compte déjà relié (get_or_create doit être idempotent).
        user = AccountService.register_client(
            email='deja_relie@dekouway.sn', password='Password123!', first_name='Old', last_name='Name'
        )
        sociallogin = _build_sociallogin('deja_relie@dekouway.sn', 'Old', 'Name')
        sociallogin.user = user

        self.adapter.save_user(self.request, sociallogin)

        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
