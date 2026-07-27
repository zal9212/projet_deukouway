from django.test import SimpleTestCase
from django.utils import timezone
from datetime import timedelta
from apps.reservations.forms import ReservationRequestForm

class ReservationsFormsTestCase(SimpleTestCase):
    def test_reservation_form_valid(self):
        today = timezone.now().date()
        form = ReservationRequestForm(data={
            'check_in': today + timedelta(days=1),
            'check_out': today + timedelta(days=5),
            'guests': 3,
            'special_requests': 'Arrivée tardive vers 20h'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['guests'], 3)

    def test_dates_invalid_checkin_past(self):
        today = timezone.now().date()
        form = ReservationRequestForm(data={
            'check_in': today - timedelta(days=2),
            'check_out': today + timedelta(days=5),
            'guests': 2
        })
        self.assertFalse(form.is_valid())
        self.assertIn('check_in', form.errors)

    def test_dates_invalid_checkout_before_checkin(self):
        today = timezone.now().date()
        form = ReservationRequestForm(data={
            'check_in': today + timedelta(days=5),
            'check_out': today + timedelta(days=2),
            'guests': 2
        })
        self.assertFalse(form.is_valid())
        self.assertIn('check_out', form.errors)

    def test_guests_zero_invalid(self):
        today = timezone.now().date()
        form = ReservationRequestForm(data={
            'check_in': today + timedelta(days=1),
            'check_out': today + timedelta(days=5),
            'guests': 0
        })
        self.assertFalse(form.is_valid())
        self.assertIn('guests', form.errors)
