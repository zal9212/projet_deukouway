from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.properties.models import PropertyCategory, PropertyType, Property

class PropertiesAPITestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@dekouway.sn', password='Password123!', is_owner=True, is_verified=True)
        self.admin = User.objects.create_user(email='admin@dekouway.sn', password='Password123!', is_superadmin=True)
        self.client_user = User.objects.create_user(email='client@dekouway.sn', password='Password123!', is_client=True)
        self.category = PropertyCategory.objects.create(name='Maison', slug='maison')
        self.property_type = PropertyType.objects.create(name='Villa', slug='villa-properties-test', category=self.category)
        self.property = Property.objects.create(
            owner=self.owner,
            property_type=self.property_type,
            title='Villa Almadies',
            description='Magnifique villa',
            price=150000,
            address='Almadies',
            city='Dakar',
            district='Almadies',
            surface=250,
            bedrooms=3,
            bathrooms=2,
            max_guests=6,
            status='PUBLISHED'
        )

    def test_list_published_properties_api(self):
        response = self.client.get('/api/v1/properties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_properties_by_city(self):
        response = self.client.get('/api/v1/properties/?city=Dakar')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_featured_properties_api(self):
        response = self.client.get('/api/v1/properties/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_categories_and_types_api(self):
        cat_res = self.client.get('/api/v1/properties/categories/')
        self.assertEqual(cat_res.status_code, status.HTTP_200_OK)

        type_res = self.client.get('/api/v1/properties/types/')
        self.assertEqual(type_res.status_code, status.HTTP_200_OK)

    def test_create_property_api(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/v1/properties/', {
            'title': 'Nouvelle Villa',
            'description': 'Superbe villa avec vue mer',
            'price': '200000.00',
            'address': 'Ngor Virage',
            'city': 'Dakar',
            'district': 'Ngor',
            'surface': 300,
            'bedrooms': 4,
            'bathrooms': 3,
            'max_guests': 8,
            'property_type_id': str(self.property_type.id)
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unverified_owner_cannot_create_property_api(self):
        unverified_owner = User.objects.create_user(
            email='unverified@dekouway.sn', password='Password123!', is_owner=True, is_verified=False
        )
        self.client.force_authenticate(user=unverified_owner)
        response = self.client.post('/api/v1/properties/', {
            'title': 'Villa non autorisée',
            'description': 'Ne devrait pas passer',
            'price': '100000.00',
            'address': 'Ngor',
            'city': 'Dakar',
            'district': 'Ngor',
            'surface': 100,
            'bedrooms': 2,
            'bathrooms': 1,
            'max_guests': 4,
            'property_type_id': str(self.property_type.id)
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_submit_property_api(self):
        draft_prop = Property.objects.create(
            owner=self.owner,
            property_type=self.property_type,
            title='Brouillon Villa',
            description='Test',
            price=100000,
            address='Fann',
            city='Dakar',
            district='Fann',
            surface=100,
            bedrooms=1,
            bathrooms=1,
            max_guests=2,
            status='DRAFT'
        )
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f'/api/v1/properties/{draft_prop.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['property']['status'], 'PENDING')

    def test_admin_approve_and_reject_property_api(self):
        pending_prop = Property.objects.create(
            owner=self.owner,
            property_type=self.property_type,
            title='En attente Villa',
            description='Test',
            price=100000,
            address='Fann',
            city='Dakar',
            district='Fann',
            surface=100,
            bedrooms=1,
            bathrooms=1,
            max_guests=2,
            status='PENDING'
        )
        self.client.force_authenticate(user=self.admin)
        approve_res = self.client.post(f'/api/v1/properties/{pending_prop.id}/approve/')
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)

    def test_owner_uploads_images_via_api(self):
        import base64
        from django.core.files.uploadedfile import SimpleUploadedFile

        draft_prop = Property.objects.create(
            owner=self.owner,
            property_type=self.property_type,
            title='Villa Photos API',
            description='Test upload API',
            price=100000,
            address='Fann',
            city='Dakar',
            district='Fann',
            surface=100,
            bedrooms=2,
            bathrooms=1,
            max_guests=4,
            status='DRAFT'
        )
        png = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        image = SimpleUploadedFile('villa.png', png, content_type='image/png')

        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f'/api/v1/properties/{draft_prop.id}/images/',
            {'images': [image]},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(draft_prop.images.count(), 1)
        self.assertTrue(draft_prop.images.first().is_cover)

    def test_toggle_favorite_api(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post('/api/v1/properties/favorites/toggle/', {
            'property_id': str(self.property.id)
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_favorite'])
