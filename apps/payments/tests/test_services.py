from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.properties.models import Property, PropertyType, PropertyCategory
from apps.reservations.models import Reservation, ReservationRequest
from apps.payments.services.services import PaymentService
from apps.payments.choices import PaymentStatusChoices, PayoutStatusChoices

class PaymentServiceTests(TestCase):
    def setUp(self):
        self.client = User.objects.create_user(email="client@test.com", password="password")
        self.owner = User.objects.create_user(email="owner@test.com", password="password")
        self.category = PropertyCategory.objects.create(name="Logement")
        self.property_type = PropertyType.objects.create(name="Maison", category=self.category)
        self.prop = Property.objects.create(
            owner=self.owner, property_type=self.property_type, title="Test", price=100.00,
            address="Addr", city="City", district="Dist", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        self.req = ReservationRequest.objects.create(
            client=self.client, property=self.prop, check_in=timezone.now().date(), check_out=timezone.now().date() + timedelta(days=2), guests=1
        )
        self.res = Reservation.objects.create(
            request=self.req, client=self.client, property=self.prop, check_in=self.req.check_in, check_out=self.req.check_out, guests=1, total_price=200.00
        )

    def test_calculate_commission(self):
        amount = Decimal('100.00')
        comm = PaymentService.calculate_commission(amount, percentage=Decimal('15.00'))
        self.assertEqual(comm, Decimal('15.00'))

    def test_full_payment_flow(self):
        # 1. Create Payment
        payment = PaymentService.create_payment(self.res, self.client, Decimal('200.00'), 'CREDIT_CARD')
        self.assertEqual(payment.status, PaymentStatusChoices.PENDING)
        
        # 2. Verify Payment
        payment = PaymentService.verify_payment(payment, 'tx_12345')
        self.assertEqual(payment.status, PaymentStatusChoices.SUCCESS)
        
        # 3. Create Commission
        commission = PaymentService.create_commission(payment)
        self.assertEqual(commission.amount, Decimal('30.00')) # 15% of 200
        
        # 4. Create Payout
        payout = PaymentService.create_payout(self.res, self.owner, 'BANK_TRANSFER')
        self.assertEqual(payout.amount, Decimal('170.00')) # 200 - 30
        self.assertEqual(payout.status, PayoutStatusChoices.PENDING)
        
        # 5. Send money
        payout = PaymentService.send_money_to_owner(payout, 'tx_67890')
        self.assertEqual(payout.status, PayoutStatusChoices.COMPLETED)
