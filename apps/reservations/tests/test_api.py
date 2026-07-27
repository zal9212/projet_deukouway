from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.properties.models import PropertyCategory, PropertyType, Property
from apps.reservations.models import ReservationRequest

class ReservationsAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@dekouway.sn', password='Password123!', is_owner=True)
        self.admin = User.objects.create_user(email='admin@dekouway.sn', password='Password123!', is_superadmin=True)
        self.client_user = User.objects.create_user(email='client@dekouway.sn', password='Password123!', is_client=True)
        self.category = PropertyCategory.objects.create(name='Maison', slug='maison')
        self.property_type = PropertyType.objects.create(name='Villa', slug='villa-reservations-test', category=self.category)
        self.property = Property.objects.create(
            owner=self.owner,
            property_type=self.property_type,
            title='Villa Somone',
            description='Villa au bord de l eau',
            price=100000,
            address='Somone',
            city='Somone',
            district='Plage',
            surface=180,
            bedrooms=2,
            bathrooms=2,
            max_guests=4,
            status='PUBLISHED'
        )

    def test_create_and_cancel_reservation_request_api(self):
        self.client.force_authenticate(user=self.client_user)
        today = timezone.now().date()
        create_res = self.client.post('/api/v1/reservations/requests/', {
            'property_id': str(self.property.id),
            'check_in': (today + timedelta(days=2)).isoformat(),
            'check_out': (today + timedelta(days=5)).isoformat(),
            'guests': 2,
            'special_requests': 'Arrivée vers 15h'
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        req_id = create_res.data['id']

        cancel_res = self.client.post(f'/api/v1/reservations/requests/{req_id}/cancel/')
        self.assertEqual(cancel_res.status_code, status.HTTP_200_OK)

    def test_admin_validate_and_owner_accept_workflow(self):
        today = timezone.now().date()
        req = ReservationRequest.objects.create(
            client=self.client_user,
            property=self.property,
            check_in=today + timedelta(days=2),
            check_out=today + timedelta(days=5),
            guests=2,
            status='REQUESTED'
        )

        self.client.force_authenticate(user=self.admin)
        val_res = self.client.post(f'/api/v1/reservations/requests/{req.id}/admin-validate/')
        self.assertEqual(val_res.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.owner)
        acc_res = self.client.post(f'/api/v1/reservations/requests/{req.id}/owner-accept/')
        self.assertEqual(acc_res.status_code, status.HTTP_200_OK)

        time_res = self.client.get(f'/api/v1/reservations/requests/{req.id}/timeline/')
        self.assertEqual(time_res.status_code, status.HTTP_200_OK)
