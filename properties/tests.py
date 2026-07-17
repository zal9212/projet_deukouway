from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Property, Amenity

User = get_user_model()

class PropertyTestCase(TestCase):
    """
    Test cases for Property listing creation, amenities mapping and moderation states.
    """
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpassword123',
            role='owner',
            is_verified_owner=True
        )
        self.wifi = Amenity.objects.create(name='Wi-Fi', icon='wifi')
        
    def test_property_creation(self):
        """Verify Property object is created with correct defaults."""
        prop = Property.objects.create(
            owner=self.owner,
            title='Jolie Villa Fann',
            description='Grande villa près de la mer.',
            property_type='villa',
            price_per_night=85000,
            address='Fann Corniche',
            city='Dakar',
            neighborhood='Fann',
            capacity=4,
            bedrooms=2,
            bathrooms=2
        )
        prop.amenities.add(self.wifi)
        
        self.assertEqual(prop.status, 'pending')  # Standard listings start as pending
        self.assertEqual(prop.price_per_night, 85000)
        self.assertIn(self.wifi, prop.amenities.all())
        self.assertTrue(prop.is_available)
