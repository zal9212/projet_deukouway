from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.properties.models import Property, PropertyType, PropertyCategory, PropertyAvailability
from apps.properties.services.services import PropertyService
from apps.properties.services.selectors import PropertySelector
from apps.properties.services.exceptions import UnauthorizedPropertyAction, InvalidPropertyStatus, DatesAlreadyBooked
from apps.properties.choices import PropertyStatusChoices

class PropertyServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@test.com", password="password", is_owner=True)
        self.other_owner = User.objects.create_user(email="other@test.com", password="password", is_owner=True)
        self.admin = User.objects.create_superuser(email="admin@dekouway.com", password="password")
        self.category = PropertyCategory.objects.create(name="Logement")
        self.property_type = PropertyType.objects.create(name="Appartement", category=self.category)

    def test_create_property(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        self.assertEqual(prop.status, PropertyStatusChoices.DRAFT)
        self.assertEqual(prop.owner, self.owner)

    def test_update_property_unauthorized(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        with self.assertRaises(UnauthorizedPropertyAction):
            PropertyService.update_property(prop, self.other_owner, title="New Title")

    def test_submit_for_validation(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        prop = PropertyService.submit_for_validation(prop, self.owner)
        self.assertEqual(prop.status, PropertyStatusChoices.PENDING)

    def test_approve_property(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        PropertyService.submit_for_validation(prop, self.owner)
        prop = PropertyService.approve_property(prop, self.admin)
        self.assertEqual(prop.status, PropertyStatusChoices.APPROVED)

    def test_publish_property(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        PropertyService.submit_for_validation(prop, self.owner)
        PropertyService.approve_property(prop, self.admin)
        prop = PropertyService.publish_property(prop, self.owner)
        self.assertEqual(prop.status, PropertyStatusChoices.PUBLISHED)

    def test_block_dates_creates_availability_rows(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        start = timezone.now().date() + timedelta(days=10)
        end = start + timedelta(days=2)
        count = PropertyService.block_dates(prop, self.owner, start, end, reason="Maintenance")
        self.assertEqual(count, 3)
        blocked = PropertySelector.get_blocked_dates(prop.id, start, end)
        self.assertEqual(len(blocked), 3)

    def test_block_dates_unauthorized_for_other_owner(self):
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        start = timezone.now().date() + timedelta(days=10)
        with self.assertRaises(UnauthorizedPropertyAction):
            PropertyService.block_dates(prop, self.other_owner, start, start)

    def test_block_dates_rejected_if_overlaps_active_booking(self):
        from apps.reservations.services.services import ReservationService
        client = User.objects.create_user(email="client@test.com", password="password", is_client=True)
        prop = PropertyService.create_property(
            self.owner, self.property_type.id, "Test Property", "Description", 100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        check_in = timezone.now().date() + timedelta(days=10)
        check_out = check_in + timedelta(days=3)
        ReservationService.create_request(client, prop, check_in, check_out, 2)

        with self.assertRaises(DatesAlreadyBooked):
            PropertyService.block_dates(prop, self.owner, check_in, check_out)
