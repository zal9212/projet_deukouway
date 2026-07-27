from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User
from apps.documents.models import DocumentCategory, Document

class DocumentsAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='docuser@dekouway.sn', password='Password123!', is_client=True)
        self.admin = User.objects.create_user(email='admin@dekouway.sn', password='Password123!', is_superadmin=True)
        self.category = DocumentCategory.objects.create(name='Contrat', slug='contrat')

    def test_upload_and_verify_document_api(self):
        self.client.force_authenticate(user=self.user)
        fake_pdf = SimpleUploadedFile('lease.pdf', b'%PDF-1.4\n%fake pdf content for tests', content_type='application/pdf')
        response = self.client.post('/api/v1/documents/', {
            'category_id': str(self.category.id),
            'title': 'Bail de location',
            'file': fake_pdf
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.data['id']

        self.client.force_authenticate(user=self.admin)
        verify_res = self.client.post(f'/api/v1/documents/{doc_id}/verify/')
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)

    def test_categories_list_api(self):
        response = self.client.get('/api/v1/documents/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
