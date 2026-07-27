from django.test import SimpleTestCase
from apps.payments.forms import PaymentForm

class PaymentsFormsTestCase(SimpleTestCase):
    def test_wave_payment_valid(self):
        form = PaymentForm(data={'method': 'WAVE', 'phone': '+221770000000'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['method'], 'WAVE')

    def test_wave_payment_missing_phone(self):
        form = PaymentForm(data={'method': 'WAVE', 'phone': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_orange_money_valid(self):
        form = PaymentForm(data={'method': 'ORANGE_MONEY', 'phone': '+221771112233'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['method'], 'ORANGE_MONEY')

    def test_credit_card_valid(self):
        form = PaymentForm(data={
            'method': 'CREDIT_CARD',
            'cardholder_name': 'Moustapha Gaye',
            'card_number': '4000123456789010',
            'card_expiry': '12/28',
            'card_cvc': '123'
        })
        self.assertTrue(form.is_valid())

    def test_credit_card_missing_cardholder(self):
        form = PaymentForm(data={'method': 'CREDIT_CARD', 'cardholder_name': '', 'card_number': '4000123456789010'})
        self.assertFalse(form.is_valid())
        self.assertIn('cardholder_name', form.errors)

    def test_credit_card_missing_card_number(self):
        form = PaymentForm(data={'method': 'CREDIT_CARD', 'cardholder_name': 'Moustapha Gaye', 'card_number': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('card_number', form.errors)
