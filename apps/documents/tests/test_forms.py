from django.test import SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.documents.forms import DocumentUploadForm

class DocumentsFormsTestCase(SimpleTestCase):
    def test_document_upload_valid(self):
        fake_pdf = SimpleUploadedFile('identity.pdf', b'PDF file content', content_type='application/pdf')
        form = DocumentUploadForm(
            data={'document_type': 'CNI', 'document_number': '123456789', 'description': 'CNI de Moustapha'},
            files={'file': fake_pdf}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['document_type'], 'CNI')

    def test_document_upload_missing_file(self):
        form = DocumentUploadForm(data={'document_type': 'CNI'})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_document_upload_invalid_extension(self):
        fake_exe = SimpleUploadedFile('script.sh', b'echo hello', content_type='text/x-shellscript')
        form = DocumentUploadForm(
            data={'document_type': 'CNI'},
            files={'file': fake_exe}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
