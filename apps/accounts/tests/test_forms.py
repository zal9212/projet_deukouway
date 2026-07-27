from django.test import SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.forms import (
    LoginForm, ClientRegisterForm, OwnerRegisterForm, ProfileForm, SecurityForm
)

class AccountsFormsTestCase(SimpleTestCase):
    def test_login_form_valid(self):
        form = LoginForm(data={'email': 'test@dekouway.sn', 'password': 'Password123!'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@dekouway.sn')
        self.assertIn('rounded-xl', form.fields['email'].widget.attrs['class'])
        self.assertEqual(form.fields['email'].widget.attrs['autocomplete'], 'email')

    def test_login_form_missing_email(self):
        form = LoginForm(data={'email': '', 'password': 'Password123!'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'], ['Veuillez renseigner votre adresse e-mail.'])

    def test_client_register_form_valid(self):
        form = ClientRegisterForm(data={
            'first_name': 'Moustapha',
            'last_name': 'Gaye',
            'email': 'moustapha@dekouway.sn',
            'phone': '+221770000000',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'accept_terms': True
        })
        self.assertTrue(form.is_valid())

    def test_client_register_form_password_mismatch(self):
        form = ClientRegisterForm(data={
            'first_name': 'Amadou',
            'last_name': 'Ndiaye',
            'email': 'amadou@dekouway.sn',
            'phone': '+221770000000',
            'password1': 'Password123!',
            'password2': 'DifferentPassword123!',
            'accept_terms': True
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertEqual(form.errors['password2'], ["Les mots de passe ne correspondent pas."])

    def test_client_register_form_invalid_phone(self):
        form = ClientRegisterForm(data={
            'first_name': 'Amadou',
            'last_name': 'Ndiaye',
            'email': 'amadou@dekouway.sn',
            'phone': 'invalid_phone_123',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'accept_terms': True
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_owner_register_form_valid(self):
        import base64
        png_bytes = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        id_file = SimpleUploadedFile('cni.jpg', png_bytes, content_type='image/jpeg')
        selfie_file = SimpleUploadedFile('selfie.jpg', png_bytes, content_type='image/jpeg')
        form = OwnerRegisterForm(
            data={
                'first_name': 'Ibrahima',
                'last_name': 'Diop',
                'email': 'owner@dekouway.sn',
                'phone': '+221771112233',
                'company_name': 'Teranga Immobilier',
                'ninea': '001234567 2G3',
                'address': 'Almadies',
                'city': 'Dakar',
                'document_type': 'CNI',
                'document_number': '1234567890123',
                'password1': 'Password123!',
                'password2': 'Password123!',
                'accept_terms': True
            },
            files={'identity_file': id_file, 'selfie_with_id_file': selfie_file}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_owner_register_form_invalid_file_extension(self):
        fake_file = SimpleUploadedFile('document.exe', b'binary content', content_type='application/x-msdownload')
        form = OwnerRegisterForm(
            data={
                'first_name': 'Ibrahima',
                'last_name': 'Diop',
                'email': 'owner@dekouway.sn',
                'phone': '+221771112233',
                'address': 'Almadies',
                'city': 'Dakar',
                'password1': 'Password123!',
                'password2': 'Password123!',
                'accept_terms': True
            },
            files={'identity_file': fake_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('identity_file', form.errors)

    def test_profile_form_valid(self):
        form = ProfileForm(data={
            'first_name': 'Fatou',
            'last_name': 'Sow',
            'phone': '+221780000000',
            'address': 'Fann Résidence',
            'city': 'Dakar',
            'country': 'Sénégal',
            'bio': 'Bienvenue chez moi !'
        })
        self.assertTrue(form.is_valid())

    def test_security_form_valid(self):
        form = SecurityForm(data={
            'old_password': 'OldPassword123!',
            'new_password': 'NewPassword123!',
            'password_confirm': 'NewPassword123!'
        })
        self.assertTrue(form.is_valid())

    def test_security_form_mismatch(self):
        form = SecurityForm(data={
            'old_password': 'OldPassword123!',
            'new_password': 'NewPassword123!',
            'password_confirm': 'DifferentPassword123!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)
