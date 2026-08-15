from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.properties.models import PropertyCategory, PropertyType, Property
from apps.reservations.models import ReservationRequest

class PaymentsAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@dekouway.sn', password='Password123!', is_owner=True)
        self.client_user = User.objects.create_user(email='client@dekouway.sn', password='Password123!', is_client=True)
        self.category = PropertyCategory.objects.create(name='Appartement', slug='appartement')
        self.property_type = PropertyType.objects.create(name='Studio', slug='studio-payments-test', category=self.category)
        self.property = Property.objects.create(
            owner=self.owner,
            property_type=self.property_type,
            title='Studio Point E',
            description='Studio meublé',
            price=40000,
            address='Point E',
            city='Dakar',
            district='Point E',
            surface=45,
            bedrooms=1,
            bathrooms=1,
            max_guests=2,
            status='PUBLISHED'
        )
        today = timezone.now().date()
        self.req = ReservationRequest.objects.create(
            client=self.client_user,
            property=self.property,
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=3),
            guests=2,
            status='PAYMENT_PENDING'
        )

    def test_process_payment_wave_api(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post('/api/v1/payments/process/', {
            'request_id': str(self.req.id),
            'method': 'WAVE',
            'phone': '+221770000000'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment', response.data)
        payment_id = response.data['payment']['id']

        receipt_res = self.client.get(f'/api/v1/payments/{payment_id}/receipt/')
        self.assertEqual(receipt_res.status_code, status.HTTP_200_OK)

    def test_invoices_and_payouts_list_api(self):
        self.client.force_authenticate(user=self.client_user)
        inv_res = self.client.get('/api/v1/payments/invoices/')
        self.assertEqual(inv_res.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.owner)
        pay_res = self.client.get('/api/v1/payments/payouts/')
        self.assertEqual(pay_res.status_code, status.HTTP_200_OK)
