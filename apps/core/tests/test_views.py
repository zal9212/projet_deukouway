from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.accounts.services.services import AccountService
from apps.properties.models import PropertyCategory, PropertyType
from apps.properties.services.services import PropertyService

class PublicViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = PropertyCategory.objects.create(name="Maison", slug="maison")
        self.type = PropertyType.objects.create(name="Villa", slug="villa-core-test", category=self.category)
        self.owner = AccountService.register_owner(
            email="owner_test@dekouway.sn",
            password="Password123!",
            first_name="Owner",
            last_name="Test"
        )
        self.property = PropertyService.create_property(
            owner=self.owner,
            property_type_id=str(self.type.id),
            title="Villa Saly Beach",
            description="Superbe villa",
            price=100000.0,
            address="Rue de la plage",
            city="Saly",
            district="Centre",
            surface=150,
            bedrooms=3,
            bathrooms=2,
            max_guests=6
        )

    def test_home_view_anonymous(self):
        response = self.client.get(reverse('public:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/public/home.html')

    def test_search_view_anonymous(self):
        response = self.client.get(reverse('public:search') + '?city=Saly')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/public/search.html')

    def test_property_detail_view_anonymous(self):
        response = self.client.get(reverse('public:property_detail', kwargs={'pk': self.property.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/public/property_detail.html')

    def test_static_public_pages(self):
        pages = ['faq', 'about', 'contact', 'legal', 'privacy', 'terms']
        for page in pages:
            response = self.client.get(reverse(f'public:{page}'))
            self.assertEqual(response.status_code, 200)

    def test_gallery_shows_real_uploaded_images_not_hardcoded_mock(self):
        import base64
        from django.core.files.uploadedfile import SimpleUploadedFile

        png_bytes = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        PropertyService.add_images(self.property, [SimpleUploadedFile('room.jpg', png_bytes, content_type='image/jpeg')])

        response = self.client.get(reverse('public:property_detail', kwargs={'pk': self.property.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/media/properties/')
        self.assertNotContains(response, 'images.unsplash.com')

    def test_property_card_wraps_entire_content_in_a_single_link(self):
        import base64
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Une image réelle est attachée pour éviter la maquette de repli (bug latent
        # et distinct : le manifeste WhiteNoise des visuels placeholder est incomplet).
        png_bytes = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        PropertyService.add_images(self.property, [SimpleUploadedFile('cover.jpg', png_bytes, content_type='image/jpeg')])
        self.property.status = 'PUBLISHED'
        self.property.save(update_fields=['status'])

        response = self.client.get(reverse('public:home'))
        self.assertEqual(response.status_code, 200)
        detail_url = reverse('public:property_detail', kwargs={'pk': self.property.id})
        # La carte apparaît sur 3 sections de la page d'accueil (2x property_card.html
        # + 1x carrousel "Logements recommandés") ; chacune ne doit contenir qu'UN SEUL
        # lien vers le détail (au lieu de 2 sur les property_card.html avant le fix).
        self.assertContains(response, f'href="{detail_url}"', count=3)


class SearchFilterTestCase(TestCase):
    """Les noms de paramètres du formulaire de recherche doivent correspondre à ceux lus par la vue."""

    def setUp(self):
        self.client = Client()
        category = PropertyCategory.objects.create(name="Logement", slug="logement-search-test")
        self.villa_type = PropertyType.objects.create(name="Villa", slug="villa-search-test", category=category)
        self.studio_type = PropertyType.objects.create(name="Studio", slug="studio-search-test", category=category)
        owner = AccountService.register_owner(
            email="search_owner@dekouway.sn", password="Password123!", first_name="Search", last_name="Owner"
        )

        self.villa = PropertyService.create_property(
            owner=owner, property_type_id=str(self.villa_type.id),
            title="Villa avec piscine", description="Grande villa", price=200000.0,
            address="Rue A", city="Saly", district="Nord",
            surface=200, bedrooms=4, bathrooms=3, max_guests=8,
        )
        self.villa.status = 'PUBLISHED'
        self.villa.save(update_fields=['status'])
        PropertyService.add_amenities(self.villa, ['Piscine', 'WiFi'])

        self.studio = PropertyService.create_property(
            owner=owner, property_type_id=str(self.studio_type.id),
            title="Petit studio centre-ville", description="Studio cosy", price=15000.0,
            address="Rue B", city="Dakar", district="Plateau",
            surface=25, bedrooms=1, bathrooms=1, max_guests=2,
        )
        self.studio.status = 'PUBLISHED'
        self.studio.save(update_fields=['status'])

    def test_keyword_search_param_matches_template_field_name(self):
        response = self.client.get(reverse('public:search'), {'search': 'piscine'})
        self.assertContains(response, 'Villa avec piscine')
        self.assertNotContains(response, 'Petit studio centre-ville')

    def test_price_range_params_match_template_field_names(self):
        response = self.client.get(reverse('public:search'), {'price_min': '10000', 'price_max': '20000'})
        self.assertContains(response, 'Petit studio centre-ville')
        self.assertNotContains(response, 'Villa avec piscine')

    def test_neighborhood_param_matches_template_field_name(self):
        response = self.client.get(reverse('public:search'), {'neighborhood': 'Plateau'})
        self.assertContains(response, 'Petit studio centre-ville')
        self.assertNotContains(response, 'Villa avec piscine')

    def test_type_filter_uses_real_property_type_slugs(self):
        response = self.client.get(reverse('public:search'), {'type': 'villa-search-test'})
        self.assertContains(response, 'Villa avec piscine')
        self.assertNotContains(response, 'Petit studio centre-ville')

    def test_bedrooms_minimum_filter(self):
        response = self.client.get(reverse('public:search'), {'bedrooms': '2'})
        self.assertContains(response, 'Villa avec piscine')
        self.assertNotContains(response, 'Petit studio centre-ville')

    def test_amenity_checkbox_filters_by_real_amenity(self):
        response = self.client.get(reverse('public:search'), {'piscine': '1'})
        self.assertContains(response, 'Villa avec piscine')
        self.assertNotContains(response, 'Petit studio centre-ville')
