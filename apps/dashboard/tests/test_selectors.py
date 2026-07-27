from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User
from apps.properties.models import Property, PropertyCategory, PropertyType, PropertyReview
from apps.reservations.models import Reservation
from apps.dashboard.services.selectors import DashboardSelector
from apps.payments.models import Payment, Commission, Payout

class DashboardSelectorTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create(email="client1@test.com", is_client=True)
        self.owner_user = User.objects.create(email="owner1@test.com", is_client=False, is_owner=True)
        
        self.category = PropertyCategory.objects.create(name="Appartement", slug="appartement")
        self.prop_type = PropertyType.objects.create(name="T2", slug="t2", category=self.category)
        
        self.property = Property.objects.create(
            title="Super Appart",
            owner=self.owner_user,
            property_type=self.prop_type,
            status="PUBLISHED",
            city="Paris",
            price=100.00,
            address="1 rue de Paris",
            surface=50,
            bedrooms=1,
            bathrooms=1,
            max_guests=2
        )
        
        from apps.reservations.models import ReservationRequest
        self.reservation_request = ReservationRequest.objects.create(
            client=self.client_user,
            property=self.property,
            check_in=timezone.now().date(),
            check_out=timezone.now().date() + timezone.timedelta(days=3),
            guests=1,
            status="REQUESTED"
        )
        
        self.reservation = Reservation.objects.create(
            request=self.reservation_request,
            property=self.property,
            client=self.client_user,
            status="CONFIRMED",
            check_in=timezone.now().date(),
            check_out=timezone.now().date() + timezone.timedelta(days=3),
            guests=1,
            total_price=300.00,
            confirmation_code="TEST1234"
        )
        
        self.review = PropertyReview.objects.create(
            property=self.property,
            user=self.client_user,
            reservation=self.reservation,
            rating=5,
            comment="Excellent stay!"
        )
        
        self.payment = Payment.objects.create(
            user=self.client_user,
            reservation=self.reservation,
            amount=300.00,
            status="SUCCESS",
            method="STRIPE"
        )
        
        Commission.objects.create(
            payment=self.payment,
            amount=30.00,
            percentage_applied=10.0
        )

    def test_owner_stats(self):
        stats = DashboardSelector.get_owner_stats(self.owner_user.id)
        self.assertEqual(stats['total_properties'], 1)
        self.assertEqual(stats['avg_rating'], 5.0)
        self.assertEqual(stats['total_reviews'], 1)
        self.assertEqual(stats['confirmed_reservations'], 1)

    def test_owner_monthly_charts(self):
        Payout.objects.create(
            owner=self.owner_user, reservation=self.reservation, amount=270.00, method='WAVE', status='COMPLETED'
        )
        charts = DashboardSelector.get_owner_monthly_charts(self.owner_user.id)
        self.assertEqual(len(charts['labels']), 6)
        self.assertEqual(len(charts['revenue_data']), 6)
        self.assertEqual(len(charts['occupancy_data']), 6)
        # Le mois courant doit refléter le revenu et l'occupation réels du fixture.
        self.assertEqual(charts['revenue_data'][-1], 270.0)
        self.assertGreater(charts['occupancy_data'][-1], 0)

    def test_admin_stats(self):
        stats = DashboardSelector.get_admin_stats()
        self.assertEqual(stats['total_clients'], 1)
        self.assertEqual(stats['total_owners'], 1)
        self.assertEqual(stats['published_properties'], 1)
        self.assertEqual(stats['total_reservations'], 1)

    def test_ai_analytics_and_insights(self):
        analytics = DashboardSelector.get_ai_analytics_and_insights()
        self.assertIn('predictions', analytics)
        self.assertIn('auto_insights', analytics)
        self.assertIn('heatmaps', analytics)
        
        insights_str = " ".join(analytics['auto_insights'])
        self.assertTrue("Paris" in insights_str or "Appartement" in insights_str or "stable" in insights_str or "Action" in insights_str)
