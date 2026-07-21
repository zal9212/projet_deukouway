from django.test import TestCase
from apps.accounts.models import User
from apps.documents.models import DocumentCategory
from apps.documents.services.services import DocumentService

class DocumentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="password")
        self.admin = User.objects.create_superuser(email="admin@test.com", password="password")
        self.category = DocumentCategory.objects.create(name="ID")

    def test_upload_document(self):
        # Using a dummy string instead of a real file for test simplicity
        doc = DocumentService.upload(self.user, self.category, "My ID", "dummy_file.jpg")
        self.assertFalse(doc.is_verified)
        self.assertEqual(doc.user, self.user)

    def test_validate_document(self):
        doc = DocumentService.upload(self.user, self.category, "My ID", "dummy_file.jpg")
        verification = DocumentService.validate_document(doc, self.admin)
        self.assertTrue(doc.is_verified)
        self.assertEqual(verification.status, 'APPROVED')
