from django.test import TestCase
from django.contrib.auth import get_user_model
from properties.models import Property
from bookings.models import Booking
from .models import Payment
import datetime

User = get_user_model()

class PaymentTestCase(TestCase):
    """
    Test cases checking payment transaction creation and ID auto-generation.
    """
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpassword123',
            role='owner',
            is_verified_owner=True
        )
        self.client = User.objects.create_user(
            username='client_test',
            email='client@test.com',
            password='testpassword123',
            role='client'
        )
        self.property = Property.objects.create(
            owner=self.owner,
            title='Studio Ngor',
            description='Studio meublé.',
            property_type='studio',
            price_per_night=30000,
            address='Ngor',
            city='Dakar',
            neighborhood='Ngor',
            status='approved'
        )
        self.booking = Booking.objects.create(
            property=self.property,
            client=self.client,
            check_in=datetime.date(2026, 8, 1),
            check_out=datetime.date(2026, 8, 5)
        )

    def test_payment_creation(self):
        """Payments should auto-generate transaction id prefixed with TXN-."""
        payment = Payment.objects.create(
            booking=self.booking,
            amount=self.booking.total_price,
            payment_method='wave',
            status='completed'
        )
        
        self.assertTrue(payment.transaction_id.startswith('TXN-'))
        self.assertEqual(payment.amount, 120000)
        self.assertEqual(payment.status, 'completed')
