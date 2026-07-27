import base64
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.services.services import AccountService
from apps.accounts.services.selectors import UserSelector

PNG_BYTES = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

class AuthViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_user = AccountService.register_client(
            email="client_test@dekouway.sn",
            password="Password123!",
            first_name="Client",
            last_name="Test"
        )
        self.owner_user = AccountService.register_owner(
            email="owner_test@dekouway.sn",
            password="Password123!",
            first_name="Owner",
            last_name="Test"
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_client_registration_flow(self):
        response = self.client.post(reverse('accounts:register_client'), {
            'email': 'new_client@dekouway.sn',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'accept_terms': 'on'
        })
        self.assertRedirects(response, reverse('dashboard:client_home'))
        new_user = UserSelector.get_user_by_email('new_client@dekouway.sn')
        self.assertIsNotNone(new_user)
        self.assertTrue(new_user.is_client)

    def test_owner_registration_flow(self):
        response = self.client.post(reverse('accounts:register_owner'), {
            'email': 'new_owner@dekouway.sn',
            'first_name': 'Paul',
            'last_name': 'Durand',
            'phone': '+221770000000',
            'address': 'Rue 10',
            'city': 'Dakar',
            'document_type': 'CNI',
            'document_number': '1234567890123',
            'identity_file': SimpleUploadedFile('cni.jpg', PNG_BYTES, content_type='image/jpeg'),
            'selfie_with_id_file': SimpleUploadedFile('selfie.jpg', PNG_BYTES, content_type='image/jpeg'),
            'password1': 'Password123!',
            'password2': 'Password123!',
            'accept_terms': 'on'
        })
        self.assertRedirects(response, reverse('accounts:owner_pending'))
        new_owner = UserSelector.get_user_by_email('new_owner@dekouway.sn')
        self.assertIsNotNone(new_owner)
        self.assertTrue(new_owner.is_owner)
        self.assertTrue(new_owner.is_active)  # Peut se connecter dès l'inscription
        self.assertFalse(new_owner.is_verified)  # Mais pas encore vérifié KYC
        identity_doc = new_owner.identity_documents.first()
        self.assertIsNotNone(identity_doc)
        self.assertTrue(identity_doc.selfie_file)

    def test_pending_owner_can_login_and_access_dashboard_but_not_publish(self):
        pending_owner = AccountService.register_owner(
            email="pending_owner@dekouway.sn", password="Password123!", first_name="Pending", last_name="Owner"
        )
        self.assertTrue(pending_owner.is_active)
        self.assertFalse(pending_owner.is_verified)

        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'pending_owner@dekouway.sn', 'password': 'Password123!',
        })
        self.assertRedirects(login_response, reverse('dashboard:owner_home'))

        dashboard_response = self.client.get(reverse('dashboard:owner_home'))
        self.assertEqual(dashboard_response.status_code, 200)

        from apps.properties.models import Property
        publish_response = self.client.post(reverse('dashboard:owner_add_property'), {
            'title': 'Villa non autorisée', 'description': 'Test', 'price': '100000',
        })
        self.assertRedirects(publish_response, reverse('dashboard:owner_add_property'))
        self.assertFalse(Property.objects.filter(title='Villa non autorisée').exists())

    def test_verified_owner_can_access_dashboard(self):
        verified_owner = AccountService.register_owner(
            email="verified_owner@dekouway.sn", password="Password123!", first_name="Verified", last_name="Owner"
        )
        AccountService.approve_owner(verified_owner, admin_user=self.owner_user)
        self.client.force_login(verified_owner)
        response = self.client.get(reverse('dashboard:owner_home'))
        self.assertEqual(response.status_code, 200)

    def test_owner_registration_rolls_back_user_if_document_upload_fails(self):
        from unittest.mock import patch
        with patch.object(AccountService, 'upload_identity_document', side_effect=Exception('boom')):
            with self.assertRaises(Exception):
                self.client.post(reverse('accounts:register_owner'), {
                    'email': 'rollback_owner@dekouway.sn',
                    'first_name': 'Rollback',
                    'last_name': 'Test',
                    'phone': '+221770000001',
                    'address': 'Rue 1',
                    'city': 'Dakar',
                    'document_type': 'CNI',
                    'document_number': '9999999999999',
                    'identity_file': SimpleUploadedFile('cni.jpg', PNG_BYTES, content_type='image/jpeg'),
                    'selfie_with_id_file': SimpleUploadedFile('selfie.jpg', PNG_BYTES, content_type='image/jpeg'),
                    'password1': 'Password123!',
                    'password2': 'Password123!',
                    'accept_terms': 'on'
                })
        self.assertIsNone(UserSelector.get_user_by_email('rollback_owner@dekouway.sn'))

    def test_post_logout_actually_logs_out_the_user(self):
        self.client.force_login(self.client_user)
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('public:home'))

        # La session doit vraiment être invalidée : la page du dashboard doit rediriger vers le login.
        dashboard_response = self.client.get(reverse('dashboard:client_home'))
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertIn(reverse('accounts:login'), dashboard_response.url)

    def test_get_logout_is_rejected_and_does_not_log_out_or_flash_success(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)

        # L'utilisateur doit rester connecté : un simple lien GET ne doit jamais déconnecter (anti-CSRF).
        dashboard_response = self.client.get(reverse('dashboard:client_home'))
        self.assertEqual(dashboard_response.status_code, 200)

        # Aucun message de déconnexion ne doit avoir été mis en file d'attente.
        messages = list(dashboard_response.context['messages'])
        self.assertFalse(any('déconnecté' in str(m) for m in messages))


class VerifyEmailViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = AccountService.register_client(
            email="verify_me@dekouway.sn", password="Password123!", first_name="Verify", last_name="Me"
        )

    def test_valid_token_verifies_email(self):
        uid, token = AccountService.generate_email_verification_token(self.user)
        response = self.client.get(reverse('accounts:verify_email') + f'?uid={uid}&token={token}')
        self.assertRedirects(response, reverse('accounts:login'))

        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_missing_token_does_not_verify_and_is_not_an_email_oracle(self):
        # L'ancienne faille : ?email=<adresse> suffisait, sans preuve de possession du compte.
        response = self.client.get(reverse('accounts:verify_email') + f'?email={self.user.email}')
        self.assertRedirects(response, reverse('public:home'))

        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_forged_token_is_rejected(self):
        uid, _ = AccountService.generate_email_verification_token(self.user)
        response = self.client.get(reverse('accounts:verify_email') + f'?uid={uid}&token=forged-token')
        self.assertRedirects(response, reverse('public:home'))

        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_token_from_another_user_does_not_verify_this_user(self):
        other_user = AccountService.register_client(
            email="other_verify@dekouway.sn", password="Password123!", first_name="Other", last_name="User"
        )
        _, other_token = AccountService.generate_email_verification_token(other_user)
        uid, _ = AccountService.generate_email_verification_token(self.user)

        response = self.client.get(reverse('accounts:verify_email') + f'?uid={uid}&token={other_token}')
        self.assertRedirects(response, reverse('public:home'))

        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)


class IdentityDocumentFileViewTestCase(TestCase):
    def setUp(self):
        from apps.accounts.models import IdentityDocument
        self.owner_user = AccountService.register_owner(
            email="doc_owner@dekouway.sn", password="Password123!", first_name="Doc", last_name="Owner"
        )
        self.other_user = AccountService.register_client(
            email="doc_other@dekouway.sn", password="Password123!", first_name="Other", last_name="Client"
        )
        self.admin_user = AccountService.register_client(
            email="doc_admin@dekouway.sn", password="Password123!", first_name="Doc", last_name="Admin"
        )
        self.admin_user.is_superuser = True
        self.admin_user.is_staff = True
        self.admin_user.save()
        AccountService.approve_owner(self.owner_user, admin_user=self.admin_user)
        self.doc = IdentityDocument.objects.create(
            user=self.owner_user, document_type='CNI', document_number='123',
            file=SimpleUploadedFile('cni.jpg', PNG_BYTES, content_type='image/jpeg'),
            selfie_file=SimpleUploadedFile('selfie.jpg', PNG_BYTES, content_type='image/jpeg'),
        )
        self.recto_url = reverse('accounts:identity_document_file', kwargs={'doc_id': self.doc.id, 'field': 'recto'})

    def test_owner_can_view_own_document(self):
        self.client.force_login(self.owner_user)
        response = self.client.get(self.recto_url)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_any_document(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.recto_url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_view_document(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.recto_url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_view_document(self):
        response = self.client.get(self.recto_url)
        self.assertEqual(response.status_code, 302)
