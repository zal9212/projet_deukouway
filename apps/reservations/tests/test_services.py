from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.properties.models import Property, PropertyType, PropertyCategory
from apps.reservations.services.services import ReservationService
from apps.reservations.services.exceptions import InvalidWorkflowTransition, DatesNotAvailable
from apps.reservations.choices import ReservationStatusChoices

class ReservationServiceTests(TestCase):
    def setUp(self):
        self.client = User.objects.create_user(email="client@test.com", password="password", is_client=True)
        self.owner = User.objects.create_user(email="owner@test.com", password="password", is_owner=True)
        self.admin = User.objects.create_superuser(email="admin@dekouway.com", password="password")
        self.category = PropertyCategory.objects.create(name="Logement")
        self.property_type = PropertyType.objects.create(name="Maison", category=self.category)
        self.prop = Property.objects.create(
            owner=self.owner, property_type=self.property_type, title="Test", description="Desc", price=100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        self.check_in = timezone.now().date() + timedelta(days=1)
        self.check_out = self.check_in + timedelta(days=3)

    def test_full_workflow(self):
        # 1. Demande par le client
        req = ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)
        self.assertEqual(req.status, ReservationStatusChoices.REQUESTED)
        
        # 2. Validation Admin
        req = ReservationService.admin_validate(req, self.admin)
        self.assertEqual(req.status, ReservationStatusChoices.SENT_TO_OWNER)
        
        # 3. Acceptation Propriétaire
        req = ReservationService.owner_accept(req, self.owner)
        self.assertEqual(req.status, ReservationStatusChoices.PAYMENT_PENDING)
        
        # 4. Paiement Confirmé
        res = ReservationService.confirm_payment(req, total_price=300.00)
        self.assertEqual(res.status, ReservationStatusChoices.CONFIRMED)
        self.assertEqual(req.status, ReservationStatusChoices.CONFIRMED)
        
        # 5. Démarrage Séjour
        res = ReservationService.start_stay(res)
        self.assertEqual(res.status, ReservationStatusChoices.CHECKIN)
        
        # 6. Fin Séjour
        res = ReservationService.finish_stay(res)
        self.assertEqual(res.status, ReservationStatusChoices.COMPLETED)

    def test_invalid_workflow_owner_accept_too_early(self):
        req = ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)
        with self.assertRaises(InvalidWorkflowTransition):
            ReservationService.owner_accept(req, self.owner)

    def test_overlapping_dates_rejected(self):
        ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)
        other_client = User.objects.create_user(email="other_client@test.com", password="password", is_client=True)
        overlapping_check_in = self.check_in + timedelta(days=1)
        overlapping_check_out = self.check_out + timedelta(days=2)
        with self.assertRaises(DatesNotAvailable):
            ReservationService.create_request(other_client, self.prop, overlapping_check_in, overlapping_check_out, 1)

    def test_non_overlapping_dates_allowed(self):
        ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)
        other_client = User.objects.create_user(email="other_client2@test.com", password="password", is_client=True)
        later_check_in = self.check_out + timedelta(days=5)
        later_check_out = later_check_in + timedelta(days=2)
        req = ReservationService.create_request(other_client, self.prop, later_check_in, later_check_out, 1)
        self.assertEqual(req.status, ReservationStatusChoices.REQUESTED)

    def test_cancelled_request_frees_up_dates(self):
        req = ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)
        ReservationService.cancel_request(req, self.client)
        other_client = User.objects.create_user(email="other_client3@test.com", password="password", is_client=True)
        new_req = ReservationService.create_request(other_client, self.prop, self.check_in, self.check_out, 1)
        self.assertEqual(new_req.status, ReservationStatusChoices.REQUESTED)

    def test_payment_link_then_contact_owner_flow(self):
        req = ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)

        admin_send = ReservationService.admin_send_payment_link(req, self.admin)
        self.assertEqual(admin_send.status, ReservationStatusChoices.PAYMENT_LINK_SENT)

        res = ReservationService.confirm_payment(admin_send, total_price=300.00)
        self.assertEqual(req.status, ReservationStatusChoices.CONFIRMED)
        self.assertEqual(res.status, ReservationStatusChoices.CONFIRMED)

        contact_res = ReservationService.contact_owner(req, self.admin)
        self.assertEqual(req.status, ReservationStatusChoices.OWNER_CONTACTED)
        self.assertEqual(contact_res.id, res.id)

    def test_send_payment_link_only_after_requested(self):
        req = ReservationService.create_request(self.client, self.prop, self.check_in, self.check_out, 2)
        ReservationService.admin_validate(req, self.admin)
        with self.assertRaises(InvalidWorkflowTransition):
            ReservationService.admin_send_payment_link(req, self.admin)
