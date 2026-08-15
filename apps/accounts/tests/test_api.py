from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User

class AccountsAPITestCase(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@dekouway.sn',
            password='Password123!',
            is_client=True
        )
        self.owner_user = User.objects.create_user(
            email='owner@dekouway.sn',
            password='Password123!',
            is_owner=True,
            is_verified=False
        )
        self.admin_user = User.objects.create_user(
            email='admin@dekouway.sn',
            password='Password123!',
            is_superadmin=True
        )

    def test_jwt_token_obtain(self):
        response = self.client.post('/api/v1/accounts/token/', {
            'email': 'client@dekouway.sn',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_register_client_api(self):
        response = self.client.post('/api/v1/accounts/auth/register-client/', {
            'email': 'newclient@dekouway.sn',
            'password': 'Password123!',
            'first_name': 'Awa',
            'last_name': 'Diop'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['email'], 'newclient@dekouway.sn')

    def test_register_owner_api(self):
        response = self.client.post('/api/v1/accounts/auth/register-owner/', {
            'email': 'newowner@dekouway.sn',
            'password': 'Password123!',
            'first_name': 'Modou',
            'last_name': 'Sow'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['email'], 'newowner@dekouway.sn')

    def test_profile_me_api(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/v1/accounts/profile/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_address_crud_api(self):
        self.client.force_authenticate(user=self.client_user)
        create_res = self.client.post('/api/v1/accounts/addresses/', {
            'street': 'Rue 10',
            'city': 'Dakar',
            'postal_code': '10000',
            'country': 'Sénégal',
            'is_default': True
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        list_res = self.client.get('/api/v1/accounts/addresses/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(list_res.data['count'], 1)

    def test_identity_document_upload_api(self):
        self.client.force_authenticate(user=self.client_user)
        fake_cni = SimpleUploadedFile('cni.pdf', b'PDF file', content_type='application/pdf')
        response = self.client.post('/api/v1/accounts/documents/', {
            'document_type': 'CNI',
            'document_number': '123456789',
            'file': fake_cni
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_approve_owner_api(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/v1/accounts/admin/users/{self.owner_user.id}/approve-owner/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['user']['is_verified'])

    def test_admin_block_unblock_user_api(self):
        self.client.force_authenticate(user=self.admin_user)
        block_res = self.client.post(f'/api/v1/accounts/admin/users/{self.client_user.id}/block/')
        self.assertEqual(block_res.status_code, status.HTTP_200_OK)

        unblock_res = self.client.post(f'/api/v1/accounts/admin/users/{self.client_user.id}/unblock/')
        self.assertEqual(unblock_res.status_code, status.HTTP_200_OK)

    def test_change_password_api(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post('/api/v1/accounts/auth/change-password/', {
            'old_password': 'Password123!',
            'new_password': 'NewPassword123!',
            'password_confirm': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_api(self):
        token_res = self.client.post('/api/v1/accounts/token/', {
            'email': 'client@dekouway.sn',
            'password': 'Password123!'
        })
        refresh = token_res.data['refresh']

        self.client.force_authenticate(user=self.client_user)
        logout_res = self.client.post('/api/v1/accounts/auth/logout/', {'refresh': refresh})
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
