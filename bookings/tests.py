from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from properties.models import Property
from .models import Booking
import datetime

User = get_user_model()

class BookingTestCase(TestCase):
    """
    Test cases checking bookings dates non-overlapping rules and price calculators.
    """
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpassword123',
            role='owner',
            is_verified_owner=True
        )
        self.client1 = User.objects.create_user(
            username='client_test1',
            email='client1@test.com',
            password='testpassword123',
            role='client'
        )
        self.client2 = User.objects.create_user(
            username='client_test2',
            email='client2@test.com',
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
            capacity=2,
            bedrooms=1,
            bathrooms=1,
            status='approved'
        )

    def test_booking_auto_pricing(self):
        """Total price should be auto calculated based on price per night and days count."""
        check_in = datetime.date(2026, 8, 1)
        check_out = datetime.date(2026, 8, 5) # 4 nights
        
        booking = Booking.objects.create(
            property=self.property,
            client=self.client1,
            check_in=check_in,
            check_out=check_out
        )
        
        self.assertEqual(booking.total_price, 120000) # 30000 * 4

    def test_overlapping_bookings_prevented(self):
        """Should raise ValidationError when bookings overlap in dates."""
        check_in = datetime.date(2026, 8, 1)
        check_out = datetime.date(2026, 8, 5)
        
        # Create first booking and approve it
        booking1 = Booking.objects.create(
            property=self.property,
            client=self.client1,
            check_in=check_in,
            check_out=check_out,
            status='approved'
        )
        
        # Try to book overlapping dates
        booking2 = Booking(
            property=self.property,
            client=self.client2,
            check_in=datetime.date(2026, 8, 3), # Overlap
            check_out=datetime.date(2026, 8, 7)
        )
        
        with self.assertRaises(ValidationError):
            booking2.full_clean()
