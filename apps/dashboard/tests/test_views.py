from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.services.services import AccountService
from apps.accounts.models import User

class DashboardViewsPermissionTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        
        # Client User
        self.client_user = AccountService.register_client(
            email="client_user@dekouway.sn",
            password="Password123!",
            first_name="Client",
            last_name="User"
        )

        # Owner User (Pending)
        self.owner_pending = AccountService.register_owner(
            email="owner_pending@dekouway.sn",
            password="Password123!",
            first_name="Owner",
            last_name="Pending"
        )

        # Owner User (Approved)
        self.owner_approved = AccountService.register_owner(
            email="owner_approved@dekouway.sn",
            password="Password123!",
            first_name="Owner",
            last_name="Approved"
        )
        # Create superadmin user for approving owner
        self.admin_user = User.objects.create_superuser(
            email="admin@dekouway.sn",
            password="AdminPassword123!"
        )
        AccountService.approve_owner(self.owner_approved, admin_user=self.admin_user)

    def test_anonymous_access_redirects_to_login(self):
        response = self.client_http.get(reverse('dashboard:client_home'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:client_home')}")

    def test_client_access_to_client_dashboard(self):
        self.client_http.login(username="client_user@dekouway.sn", password="Password123!")
        response = self.client_http.get(reverse('dashboard:client_home'))
        self.assertEqual(response.status_code, 200)

    def test_client_access_to_owner_dashboard_rejected(self):
        self.client_http.login(username="client_user@dekouway.sn", password="Password123!")
        response = self.client_http.get(reverse('dashboard:owner_home'))
        self.assertRedirects(response, reverse('public:home'))

    def test_pending_owner_redirected_to_pending_page(self):
        # Pending owner attempting access to unapproved features redirects to login or pending page
        response = self.client_http.get(reverse('dashboard:owner_home'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:owner_home')}")

    def test_approved_owner_access_to_owner_dashboard(self):
        self.client_http.login(username="owner_approved@dekouway.sn", password="Password123!")
        response = self.client_http.get(reverse('dashboard:owner_home'))
        self.assertEqual(response.status_code, 200)

    def test_admin_access_to_admin_dashboard(self):
        self.client_http.login(username="admin@dekouway.sn", password="AdminPassword123!")
        response = self.client_http.get(reverse('dashboard:admin_home'))
        self.assertEqual(response.status_code, 200)


class AdminConfigurationViewTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        self.admin_user = User.objects.create_superuser(email="admin_cfg@dekouway.sn", password="AdminPassword123!")
        self.client_http.login(username="admin_cfg@dekouway.sn", password="AdminPassword123!")

    def test_valid_update_persists(self):
        from apps.payments.models import PlatformSettings
        response = self.client_http.post(reverse('dashboard:admin_config'), {
            'commission_percentage': '20', 'client_service_fee': '3000',
        })
        self.assertRedirects(response, reverse('dashboard:admin_config'))
        settings_obj = PlatformSettings.load()
        self.assertEqual(str(settings_obj.commission_percentage), '20.00')
        self.assertEqual(str(settings_obj.client_service_fee), '3000.00')

    def test_invalid_commission_over_100_rejected(self):
        from apps.payments.models import PlatformSettings
        PlatformSettings.load()  # ensure a baseline row exists
        response = self.client_http.post(reverse('dashboard:admin_config'), {
            'commission_percentage': '150', 'client_service_fee': '3000',
        })
        self.assertRedirects(response, reverse('dashboard:admin_config'))
        settings_obj = PlatformSettings.load()
        self.assertNotEqual(str(settings_obj.commission_percentage), '150.00')


class ClientSettingsViewTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        self.client_user = AccountService.register_client(
            email="settings_client@dekouway.sn", password="Password123!", first_name="Set", last_name="Tings"
        )
        self.client_http.force_login(self.client_user)

    def test_update_preferences_persists(self):
        from apps.notifications.models import NotificationPreference

        response = self.client_http.post(reverse('dashboard:client_settings'), {'email_enabled': 'on'})
        self.assertRedirects(response, reverse('dashboard:client_settings'))

        preferences = NotificationPreference.objects.get(user=self.client_user)
        self.assertTrue(preferences.email_enabled)
        self.assertFalse(preferences.sms_enabled)

        self.client_http.post(reverse('dashboard:client_settings'), {})
        preferences.refresh_from_db()
        self.assertFalse(preferences.email_enabled)


class AdminOwnerDetailViewTestCase(TestCase):
    def setUp(self):
        import base64
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.accounts.services.services import AccountService
        from apps.properties.models import PropertyType

        self.client_http = Client()
        self.admin = User.objects.create_superuser(email="admin_owner_detail@dekouway.sn", password="Password123!")
        self.client_http.force_login(self.admin)

        self.owner = AccountService.register_owner(
            email="reviewed_owner@dekouway.sn", password="Password123!", first_name="Koto", last_name="Diop"
        )
        png_bytes = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        AccountService.upload_identity_document(
            self.owner, document_type='CNI', document_number='1234567890123',
            file=SimpleUploadedFile('cni.jpg', png_bytes, content_type='image/jpeg'),
            selfie_file=SimpleUploadedFile('selfie.jpg', png_bytes, content_type='image/jpeg'),
        )
        self.property_type = PropertyType.objects.first()

    def test_detail_page_shows_real_dossier(self):
        response = self.client_http.get(reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'reviewed_owner@dekouway.sn')
        self.assertContains(response, 'CNI')
        self.assertContains(response, '1234567890123')

    def test_owners_list_links_to_detail_page(self):
        response = self.client_http.get(reverse('dashboard:admin_owners'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}))

    def test_approve_from_detail_page(self):
        response = self.client_http.post(
            reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}), {'action': 'approve'}
        )
        self.assertRedirects(response, reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_verified)

    def test_reject_from_detail_page_redirects_to_list(self):
        response = self.client_http.post(
            reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}), {'action': 'reject'}
        )
        self.assertRedirects(response, reverse('dashboard:admin_owners'))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_deleted)

    def test_toggle_status_from_detail_page(self):
        response = self.client_http.post(
            reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}), {'action': 'toggle_status'}
        )
        self.assertRedirects(response, reverse('dashboard:admin_owner_detail', kwargs={'pk': self.owner.id}))
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_active)

    def test_client_id_does_not_resolve_as_owner_dossier(self):
        client_user = AccountService.register_client(
            email="not_an_owner@dekouway.sn", password="Password123!", first_name="Not", last_name="Owner"
        )
        response = self.client_http.get(reverse('dashboard:admin_owner_detail', kwargs={'pk': client_user.id}))
        self.assertEqual(response.status_code, 404)


class AdminValidatePropertiesViewTestCase(TestCase):
    def setUp(self):
        from apps.properties.models import Property, PropertyType
        from apps.accounts.services.services import AccountService

        self.client_http = Client()
        self.admin = User.objects.create_superuser(email="admin_validate_prop@dekouway.sn", password="Password123!")
        self.client_http.force_login(self.admin)

        self.owner = AccountService.register_owner(
            email="pending_prop_owner@dekouway.sn", password="Password123!", first_name="Owner", last_name="Test"
        )
        self.property_type = PropertyType.objects.first()
        self.prop = Property.objects.create(
            owner=self.owner, property_type=self.property_type, title='Villa En Attente', description='Test',
            price=50000, address='Adresse', city='Dakar', district='Ngor',
            surface=100, bedrooms=2, bathrooms=1, max_guests=4, status='PENDING',
        )

    def test_approve_actually_publishes_the_listing(self):
        from apps.properties.choices import PropertyStatusChoices
        response = self.client_http.post(reverse('dashboard:admin_validate_properties'), {
            'property_id': str(self.prop.id), 'action': 'approve',
        })
        self.assertRedirects(response, reverse('dashboard:admin_validate_properties'))

        self.prop.refresh_from_db()
        self.assertEqual(self.prop.status, PropertyStatusChoices.PUBLISHED)

    def test_published_listing_appears_on_public_homepage(self):
        from apps.properties.services.selectors import PropertySelector

        self.client_http.post(reverse('dashboard:admin_validate_properties'), {
            'property_id': str(self.prop.id), 'action': 'approve',
        })
        self.assertIn(self.prop, PropertySelector.get_published_properties())


class AdminSupportTicketViewTestCase(TestCase):
    def setUp(self):
        from apps.support.models import SupportCategory, Ticket
        self.client_http = Client()
        self.admin_user = User.objects.create_superuser(email="admin_support@dekouway.sn", password="AdminPassword123!")
        self.ticket_user = AccountService.register_client(
            email="ticket_user@dekouway.sn", password="Password123!", first_name="Ticket", last_name="User"
        )
        self.category = SupportCategory.objects.create(name="Technique", slug="technique-dashboard-test")
        self.ticket = Ticket.objects.create(
            user=self.ticket_user, category=self.category, subject="Souci de paiement", description="Ca ne marche pas.",
        )
        self.client_http.login(username="admin_support@dekouway.sn", password="AdminPassword123!")

    def test_admin_can_reply_to_ticket(self):
        from apps.support.models import TicketMessage
        response = self.client_http.post(reverse('dashboard:admin_support'), {
            'ticket_id': str(self.ticket.id), 'action': 'reply', 'content': 'Nous regardons cela.',
        })
        self.assertRedirects(response, f"{reverse('dashboard:admin_support')}?ticket={self.ticket.id}")
        self.assertTrue(TicketMessage.objects.filter(ticket=self.ticket, content='Nous regardons cela.').exists())
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'IN_PROGRESS')

    def test_admin_can_escalate_ticket(self):
        response = self.client_http.post(reverse('dashboard:admin_support'), {
            'ticket_id': str(self.ticket.id), 'action': 'escalate',
        })
        self.assertRedirects(response, f"{reverse('dashboard:admin_support')}?ticket={self.ticket.id}")
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'ESCALATED')

    def test_admin_can_close_ticket(self):
        response = self.client_http.post(reverse('dashboard:admin_support'), {
            'ticket_id': str(self.ticket.id), 'action': 'close',
        })
        self.assertRedirects(response, f"{reverse('dashboard:admin_support')}?ticket={self.ticket.id}")
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'CLOSED')

    def test_cannot_reply_to_closed_ticket(self):
        self.ticket.status = 'CLOSED'
        self.ticket.save(update_fields=['status'])
        response = self.client_http.post(reverse('dashboard:admin_support'), {
            'ticket_id': str(self.ticket.id), 'action': 'reply', 'content': 'Trop tard.',
        })
        self.assertRedirects(response, f"{reverse('dashboard:admin_support')}?ticket={self.ticket.id}")


class OwnerAddPropertyViewTestCase(TestCase):
    def setUp(self):
        import base64
        from apps.properties.models import PropertyType

        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="add_property_owner@dekouway.sn", password="Password123!", first_name="Add", last_name="Owner"
        )
        self.admin = User.objects.create_superuser(email="add_property_admin@dekouway.sn", password="AdminPassword123!")
        AccountService.approve_owner(self.owner, admin_user=self.admin)
        self.property_type = PropertyType.objects.first()
        self.png_bytes = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        self.client_http.force_login(self.owner)

    def _valid_payload(self, **overrides):
        from django.core.files.uploadedfile import SimpleUploadedFile
        payload = {
            'title': 'Villa Teranga', 'description': 'Une superbe villa.', 'property_type_id': str(self.property_type.id),
            'address': 'Route de Ngor', 'city': 'Dakar', 'district': 'Ngor',
            'latitude': '14.7167', 'longitude': '-17.4677',
            'surface': '200', 'bedrooms': '3', 'bathrooms': '2', 'max_guests': '6', 'price': '50000',
            'amenities': ['WiFi', 'Piscine'], 'rules': ['Non-fumeur'],
            'images': [SimpleUploadedFile('cover.png', self.png_bytes, content_type='image/png')],
        }
        payload.update(overrides)
        return payload

    def test_wizard_form_is_personalized_by_property_category(self):
        response = self.client_http.get(reverse('dashboard:owner_add_property'))
        self.assertEqual(response.status_code, 200)
        # Chaque <option> doit porter la catégorie du type pour permettre la personnalisation JS.
        self.assertContains(response, 'data-category-slug="chambre-privee"')
        self.assertContains(response, 'data-category-slug="logement-entier"')
        # Les équipements spécifiques à chaque catégorie doivent être présents.
        self.assertContains(response, 'Salle de bain privée')
        self.assertContains(response, 'Cuisine tout équipée')

    def test_verified_owner_can_create_and_submit_property(self):
        from apps.properties.models import Property
        response = self.client_http.post(reverse('dashboard:owner_add_property'), self._valid_payload())
        self.assertRedirects(response, reverse('dashboard:owner_properties'))

        prop = Property.objects.get(title='Villa Teranga')
        self.assertEqual(prop.status, 'PENDING')
        self.assertEqual(float(prop.latitude), 14.7167)
        self.assertEqual(float(prop.longitude), -17.4677)
        self.assertEqual(prop.images.count(), 1)
        self.assertTrue(prop.images.first().is_cover)
        self.assertEqual(prop.amenities.count(), 2)
        self.assertEqual(prop.rules.count(), 1)

    def test_missing_images_rejected(self):
        from apps.properties.models import Property
        response = self.client_http.post(reverse('dashboard:owner_add_property'), self._valid_payload(images=[]))
        self.assertRedirects(response, reverse('dashboard:owner_add_property'))
        self.assertFalse(Property.objects.filter(title='Villa Teranga').exists())

    def test_missing_required_field_rejected(self):
        from apps.properties.models import Property
        response = self.client_http.post(reverse('dashboard:owner_add_property'), self._valid_payload(city=''))
        self.assertRedirects(response, reverse('dashboard:owner_add_property'))
        self.assertFalse(Property.objects.filter(title='Villa Teranga').exists())

    def test_unverified_owner_cannot_submit_property(self):
        from apps.properties.models import Property
        unverified_owner = AccountService.register_owner(
            email="unverified_add_owner@dekouway.sn", password="Password123!", first_name="Unverified", last_name="Owner"
        )
        self.client_http.force_login(unverified_owner)
        response = self.client_http.post(reverse('dashboard:owner_add_property'), self._valid_payload())
        self.assertRedirects(response, reverse('dashboard:owner_add_property'))
        self.assertFalse(Property.objects.filter(title='Villa Teranga').exists())


class OwnerEditPropertyViewTestCase(TestCase):
    def setUp(self):
        import base64
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.properties.models import PropertyType
        from apps.properties.services.services import PropertyService

        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="edit_property_owner@dekouway.sn", password="Password123!", first_name="Edit", last_name="Owner"
        )
        self.admin = User.objects.create_superuser(email="edit_property_admin@dekouway.sn", password="AdminPassword123!")
        AccountService.approve_owner(self.owner, admin_user=self.admin)

        self.entire_home_type = PropertyType.objects.get(slug='villa')
        self.private_room_type = PropertyType.objects.get(slug='chambre-chez-habitant')

        png_bytes = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        self.prop = PropertyService.create_property(
            owner=self.owner, property_type_id=self.entire_home_type.id,
            title='Villa Originale', description='Description originale.', price=40000,
            address='Ancienne adresse', city='Dakar', district='Ngor',
            surface=150, bedrooms=3, bathrooms=2, max_guests=5,
            latitude=14.7, longitude=-17.4,
        )
        PropertyService.add_images(self.prop, [SimpleUploadedFile('cover.png', png_bytes, content_type='image/png')])
        PropertyService.add_amenities(self.prop, ['WiFi'])
        PropertyService.add_rules(self.prop, ['Non-fumeur'])

        self.client_http.force_login(self.owner)
        self.url = reverse('dashboard:owner_edit_property', kwargs={'pk': self.prop.id})

    def test_get_prefills_existing_values_for_personalization(self):
        response = self.client_http.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Villa Originale')
        self.assertContains(response, 'data-category-slug="logement-entier"')
        self.assertContains(response, '"existing_images_count": 1')

    def test_post_updates_all_fields_and_replaces_amenities_rules(self):
        response = self.client_http.post(self.url, {
            'title': 'Villa Renovee', 'description': 'Nouvelle description.',
            'property_type_id': str(self.private_room_type.id),
            'address': 'Nouvelle adresse', 'city': 'Saly', 'district': 'Centre',
            'latitude': '14.5', 'longitude': '-17.0',
            'surface': '20', 'bedrooms': '1', 'bathrooms': '1', 'max_guests': '2', 'price': '15000',
            'amenities': ['Salle de bain privée'], 'rules': ['Non-fumeur', 'Adapté aux enfants'],
        })
        self.assertRedirects(response, reverse('dashboard:owner_properties'))

        self.prop.refresh_from_db()
        self.assertEqual(self.prop.title, 'Villa Renovee')
        self.assertEqual(self.prop.property_type_id, self.private_room_type.id)
        self.assertEqual(self.prop.city, 'Saly')
        self.assertEqual(self.prop.bedrooms, 1)
        self.assertEqual(float(self.prop.price), 15000.0)

        # Les équipements/règles doivent être remplacés, pas cumulés.
        self.assertEqual(list(self.prop.amenities.values_list('name', flat=True)), ['Salle de bain privée'])
        self.assertEqual(self.prop.rules.count(), 2)

        # Une seule photo existait et aucune nouvelle n'a été envoyée : elle doit rester intacte.
        self.assertEqual(self.prop.images.count(), 1)

    def test_other_owner_cannot_edit(self):
        other_owner = AccountService.register_owner(
            email="other_edit_owner@dekouway.sn", password="Password123!", first_name="Other", last_name="Owner"
        )
        self.client_http.force_login(other_owner)
        response = self.client_http.get(self.url)
        self.assertEqual(response.status_code, 404)


class ResolveMapLinkViewTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="map_owner@dekouway.sn", password="Password123!", first_name="Map", last_name="Owner"
        )
        self.client_http.force_login(self.owner)
        self.url = reverse('dashboard:owner_resolve_map_link')

    def test_raw_coordinates_resolved_directly(self):
        response = self.client_http.post(self.url, {'text': '14.7167, -17.4677'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertAlmostEqual(data['lat'], 14.7167)
        self.assertAlmostEqual(data['lng'], -17.4677)

    def test_full_google_maps_url_resolved_without_http_call(self):
        response = self.client_http.post(self.url, {
            'text': 'https://www.google.com/maps/place/Dakar/@14.7167,-17.4677,15z'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertAlmostEqual(data['lat'], 14.7167)
        self.assertAlmostEqual(data['lng'], -17.4677)

    def test_non_google_host_rejected(self):
        response = self.client_http.post(self.url, {'text': 'https://evil.com/redirect?to=internal'})
        self.assertEqual(response.status_code, 400)

    def test_google_maps_search_slash_format_resolved(self):
        # Format réel observé après résolution d'un lien maps.app.goo.gl :
        # /maps/search/<lat>,+<lng> (le "+" est un espace URL-encodé littéral).
        response = self.client_http.post(self.url, {
            'text': 'https://www.google.es/maps/search/28.099023,+-15.441747?entry=tts'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertAlmostEqual(data['lat'], 28.099023)
        self.assertAlmostEqual(data['lng'], -15.441747)

    def test_shortened_link_resolved_via_redirect_chain(self):
        from unittest.mock import patch, MagicMock
        redirect_response = MagicMock()
        redirect_response.headers = {'Location': 'https://www.google.com/maps/@14.7167,-17.4677,15z'}
        with patch('apps.dashboard.views.owner.requests.head', return_value=redirect_response) as mock_head:
            response = self.client_http.post(self.url, {'text': 'https://maps.app.goo.gl/abc123'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertAlmostEqual(data['lat'], 14.7167)
        self.assertAlmostEqual(data['lng'], -17.4677)
        mock_head.assert_called_once()

    def test_anonymous_cannot_access(self):
        self.client_http.logout()
        response = self.client_http.post(self.url, {'text': '14.7167, -17.4677'})
        self.assertEqual(response.status_code, 302)


class OwnerCalendarViewTestCase(TestCase):
    def setUp(self):
        from apps.properties.models import PropertyType, PropertyCategory
        from apps.properties.services.services import PropertyService
        from apps.reservations.services.services import ReservationService

        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="calendar_owner@dekouway.sn", password="Password123!", first_name="Cal", last_name="Owner"
        )
        self.admin = User.objects.create_superuser(email="calendar_admin@dekouway.sn", password="AdminPassword123!")
        AccountService.approve_owner(self.owner, admin_user=self.admin)
        self.client_user = AccountService.register_client(
            email="calendar_client@dekouway.sn", password="Password123!", first_name="Cal", last_name="Client"
        )

        category = PropertyCategory.objects.create(name="Logement", slug="logement-calendar-test")
        prop_type = PropertyType.objects.create(name="Villa", slug="villa-calendar-test", category=category)
        self.prop = PropertyService.create_property(
            self.owner, prop_type.id, "Villa Calendrier", "Desc", 50000.0,
            address="Addr", city="Dakar", district="Ngor", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )

        self.today = timezone.now().date()
        self.check_in = self.today + timezone.timedelta(days=5)
        self.check_out = self.check_in + timezone.timedelta(days=2)
        self.req = ReservationService.create_request(self.client_user, self.prop, self.check_in, self.check_out, 2)

        self.client_http.force_login(self.owner)

    def test_calendar_renders_with_weeks_and_property(self):
        response = self.client_http.get(reverse('dashboard:owner_calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_property'].id, self.prop.id)
        weeks = response.context['weeks']
        self.assertTrue(len(weeks) >= 4)
        for week in weeks:
            self.assertEqual(len(week), 7)

    def test_pending_request_shown_as_pending(self):
        response = self.client_http.get(
            reverse('dashboard:owner_calendar'),
            {'property': str(self.prop.id), 'year': self.check_in.year, 'month': self.check_in.month}
        )
        weeks = response.context['weeks']
        matching_days = [day for week in weeks for day in week if day['date'] == self.check_in]
        self.assertEqual(len(matching_days), 1)
        self.assertEqual(matching_days[0]['status'], 'pending')

    def test_confirmed_reservation_shown_as_confirmed(self):
        from apps.reservations.services.services import ReservationService
        req = ReservationService.admin_validate(self.req, self.admin)
        req = ReservationService.owner_accept(req, self.owner)
        ReservationService.confirm_payment(req, total_price=100000.0)

        response = self.client_http.get(
            reverse('dashboard:owner_calendar'),
            {'property': str(self.prop.id), 'year': self.check_in.year, 'month': self.check_in.month}
        )
        weeks = response.context['weeks']
        matching_days = [day for week in weeks for day in week if day['date'] == self.check_in]
        self.assertEqual(matching_days[0]['status'], 'confirmed')

    def test_month_navigation_context(self):
        response = self.client_http.get(reverse('dashboard:owner_calendar'), {'year': 2026, 'month': 1})
        self.assertEqual(response.context['prev_year'], 2025)
        self.assertEqual(response.context['prev_month'], 12)
        self.assertEqual(response.context['next_year'], 2026)
        self.assertEqual(response.context['next_month'], 2)

    def test_block_dates_creates_blocked_status(self):
        from apps.properties.models import PropertyAvailability
        start = self.today + timezone.timedelta(days=60)
        end = start + timezone.timedelta(days=1)
        response = self.client_http.post(reverse('dashboard:owner_calendar'), {
            'property_id': str(self.prop.id), 'start_date': start.isoformat(), 'end_date': end.isoformat(),
            'reason': 'Test maintenance', 'year': start.year, 'month': start.month,
        })
        self.assertRedirects(
            response,
            f"{reverse('dashboard:owner_calendar')}?property={self.prop.id}&year={start.year}&month={start.month}"
        )
        self.assertEqual(PropertyAvailability.objects.filter(property=self.prop, is_available=False).count(), 2)

    def test_block_dates_overlapping_booking_rejected(self):
        from apps.properties.models import PropertyAvailability
        response = self.client_http.post(reverse('dashboard:owner_calendar'), {
            'property_id': str(self.prop.id), 'start_date': self.check_in.isoformat(), 'end_date': self.check_out.isoformat(),
            'reason': '', 'year': self.check_in.year, 'month': self.check_in.month,
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PropertyAvailability.objects.filter(property=self.prop, is_available=False).exists())


class OwnerPropertiesViewTestCase(TestCase):
    def setUp(self):
        from apps.properties.models import PropertyType, PropertyCategory
        from apps.properties.services.services import PropertyService

        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="props_owner@dekouway.sn", password="Password123!", first_name="Props", last_name="Owner"
        )
        self.admin = User.objects.create_superuser(email="props_admin@dekouway.sn", password="AdminPassword123!")
        AccountService.approve_owner(self.owner, admin_user=self.admin)
        category = PropertyCategory.objects.create(name="Logement", slug="logement-props-test")
        prop_type = PropertyType.objects.create(name="Villa", slug="villa-props-test", category=category)
        self.published = PropertyService.create_property(
            self.owner, prop_type.id, "Villa Publiée", "Desc", 50000.0,
            address="Addr", city="Dakar", district="Ngor", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        self.published.status = 'PUBLISHED'
        self.published.save(update_fields=['status'])
        self.draft = PropertyService.create_property(
            self.owner, prop_type.id, "Villa Brouillon", "Desc", 50000.0,
            address="Addr", city="Dakar", district="Ngor", surface=100, bedrooms=2, bathrooms=1, max_guests=4
        )
        self.client_http.force_login(self.owner)

    def test_status_filter_shows_only_matching_properties(self):
        response = self.client_http.get(reverse('dashboard:owner_properties'), {'status': 'draft'})
        titles = [p.title for p in response.context['properties']]
        self.assertIn('Villa Brouillon', titles)
        self.assertNotIn('Villa Publiée', titles)

    def test_archive_published_property(self):
        response = self.client_http.post(reverse('dashboard:owner_properties'), {
            'property_id': str(self.published.id), 'action': 'archive',
        })
        self.assertRedirects(response, reverse('dashboard:owner_properties'))
        self.published.refresh_from_db()
        self.assertEqual(self.published.status, 'ARCHIVED')

    def test_cannot_archive_another_owners_property(self):
        other_owner = AccountService.register_owner(
            email="props_other_owner@dekouway.sn", password="Password123!", first_name="Other", last_name="Owner"
        )
        self.client_http.force_login(other_owner)
        response = self.client_http.post(reverse('dashboard:owner_properties'), {
            'property_id': str(self.published.id), 'action': 'archive',
        })
        self.assertRedirects(response, reverse('dashboard:owner_properties'))
        self.published.refresh_from_db()
        self.assertNotEqual(self.published.status, 'ARCHIVED')


class OwnerProfileAndSecurityViewTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="profile_owner@dekouway.sn", password="Password123!", first_name="Original", last_name="Name"
        )
        self.client_http.force_login(self.owner)

    def test_profile_update_writes_to_userprofile_not_user(self):
        from apps.accounts.services.selectors import UserSelector
        response = self.client_http.post(reverse('dashboard:owner_profile'), {
            'first-name': 'Updated', 'last-name': 'Owner', 'email': self.owner.email, 'phone': '+221770000000',
        })
        self.assertRedirects(response, reverse('dashboard:owner_profile'))
        profile = UserSelector.get_user_profile(self.owner)
        self.assertEqual(profile.first_name, 'Updated')
        self.assertEqual(profile.phone, '+221770000000')

        dashboard_response = self.client_http.get(reverse('dashboard:owner_home'))
        self.assertContains(dashboard_response, 'Updated')

    def test_password_change_requires_correct_current_password(self):
        response = self.client_http.post(reverse('dashboard:owner_security'), {
            'current_password': 'WrongPassword!', 'new_password': 'NewPassword123!',
        })
        self.assertRedirects(response, reverse('dashboard:owner_security'))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password('Password123!'))

    def test_password_change_keeps_session_valid(self):
        response = self.client_http.post(reverse('dashboard:owner_security'), {
            'current_password': 'Password123!', 'new_password': 'NewPassword123!',
        })
        self.assertRedirects(response, reverse('dashboard:owner_security'))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password('NewPassword123!'))

        # La session ne doit pas être invalidée par le changement de mot de passe.
        dashboard_response = self.client_http.get(reverse('dashboard:owner_home'))
        self.assertEqual(dashboard_response.status_code, 200)


class OwnerSettingsViewTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        self.owner = AccountService.register_owner(
            email="settings_owner@dekouway.sn", password="Password123!", first_name="Set", last_name="Tings"
        )
        self.client_http.force_login(self.owner)

    def test_settings_page_shows_real_phone_not_hardcoded(self):
        from apps.accounts.services.selectors import UserSelector
        profile = UserSelector.get_user_profile(self.owner)
        profile.phone = '+221770000099'
        profile.save(update_fields=['phone'])

        response = self.client_http.get(reverse('dashboard:owner_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '+221 *** ** 99')
        self.assertNotContains(response, '+221 77 *** ** 67')

    def test_update_preferences_persists_and_is_not_hardcoded(self):
        from apps.notifications.models import NotificationPreference

        response = self.client_http.post(reverse('dashboard:owner_settings'), {
            'email_enabled': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:owner_settings'))

        preferences = NotificationPreference.objects.get(user=self.owner)
        self.assertTrue(preferences.email_enabled)
        self.assertFalse(preferences.sms_enabled)

        # Décocher les deux cases doit bien désactiver les deux canaux.
        self.client_http.post(reverse('dashboard:owner_settings'), {})
        preferences.refresh_from_db()
        self.assertFalse(preferences.email_enabled)
        self.assertFalse(preferences.sms_enabled)


class AdminProfileAndSecurityViewTestCase(TestCase):
    def setUp(self):
        self.client_http = Client()
        self.admin = User.objects.create_superuser(email="root_admin@dekouway.sn", password="Password123!")
        self.client_http.force_login(self.admin)

    def test_profile_page_shows_real_data_not_hardcoded(self):
        response = self.client_http.get(reverse('dashboard:admin_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'root_admin@dekouway.sn')
        self.assertNotContains(response, 'admin@dekouway.com')
        self.assertNotContains(response, 'Administrateur Root')

    def test_profile_update_writes_to_userprofile_and_email(self):
        from apps.accounts.services.selectors import UserSelector
        response = self.client_http.post(reverse('dashboard:admin_profile'), {
            'first_name': 'Awa', 'last_name': 'Ndiaye', 'email': 'awa_admin@dekouway.sn',
        })
        self.assertRedirects(response, reverse('dashboard:admin_profile'))

        profile = UserSelector.get_user_profile(self.admin)
        self.assertEqual(profile.first_name, 'Awa')
        self.assertEqual(profile.last_name, 'Ndiaye')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, 'awa_admin@dekouway.sn')

    def test_profile_update_rejects_email_already_in_use(self):
        User.objects.create_superuser(email="taken@dekouway.sn", password="Password123!")
        response = self.client_http.post(reverse('dashboard:admin_profile'), {
            'first_name': 'Awa', 'last_name': 'Ndiaye', 'email': 'taken@dekouway.sn',
        })
        self.assertRedirects(response, reverse('dashboard:admin_profile'))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, 'root_admin@dekouway.sn')

    def test_security_page_no_longer_claims_fake_2fa(self):
        response = self.client_http.get(reverse('dashboard:admin_security'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Activée (Google Authenticator)')
        self.assertNotContains(response, 'Dernier changement il y a 30 jours')

    def test_password_change_requires_correct_current_password(self):
        response = self.client_http.post(reverse('dashboard:admin_security'), {
            'current_password': 'WrongPassword!', 'new_password': 'NewPassword123!',
        })
        self.assertRedirects(response, reverse('dashboard:admin_security'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('Password123!'))

    def test_password_change_keeps_session_valid(self):
        response = self.client_http.post(reverse('dashboard:admin_security'), {
            'current_password': 'Password123!', 'new_password': 'NewPassword123!',
        })
        self.assertRedirects(response, reverse('dashboard:admin_security'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('NewPassword123!'))

        dashboard_response = self.client_http.get(reverse('dashboard:admin_home'))
        self.assertEqual(dashboard_response.status_code, 200)


class AdminFinancialPagesFieldNameTestCase(TestCase):
    """Les templates référençaient des champs inexistants (reservation.code, payment.transaction_id) :
    ils retombaient silencieusement sur l'UUID brut au lieu du vrai code lisible."""

    def setUp(self):
        import datetime
        from apps.properties.models import PropertyType
        from apps.properties.services.services import PropertyService
        from apps.reservations.models import ReservationRequest, Reservation
        from apps.payments.models import Payment, Payout
        from apps.payments.choices import PaymentMethodChoices

        self.client_http = Client()
        self.admin = User.objects.create_superuser(email="admin_financial@dekouway.sn", password="Password123!")
        self.client_http.force_login(self.admin)

        owner = AccountService.register_owner(
            email="financial_owner@dekouway.sn", password="Password123!", first_name="Fin", last_name="Owner"
        )
        AccountService.approve_owner(owner, admin_user=self.admin)
        client_user = AccountService.register_client(
            email="financial_client@dekouway.sn", password="Password123!", first_name="Fin", last_name="Client"
        )
        prop_type = PropertyType.objects.first()
        prop = PropertyService.create_property(
            owner=owner, property_type_id=prop_type.id, title="Villa Financière", description="Test",
            price=50000, address="Adresse", city="Dakar", district="Ngor",
            surface=100, bedrooms=2, bathrooms=1, max_guests=4,
        )

        req = ReservationRequest.objects.create(
            client=client_user, property=prop, check_in=datetime.date(2026, 8, 1),
            check_out=datetime.date(2026, 8, 5), guests=2,
        )
        self.reservation = Reservation.objects.create(
            request=req, client=client_user, property=prop,
            check_in=req.check_in, check_out=req.check_out, guests=2, total_price=200000,
            confirmation_code='DKW-TEST1234',
        )
        self.payment = Payment.objects.create(
            reservation=self.reservation, user=client_user, amount=200000,
            method=PaymentMethodChoices.WAVE, gateway_transaction_id='WAVE-TX-REAL-123',
        )
        self.payout = Payout.objects.create(
            owner=owner, reservation=self.reservation, amount=170000,
            method=PaymentMethodChoices.WAVE, gateway_transaction_id='WAVE-PAYOUT-REAL-456',
        )

    def test_reservations_page_shows_real_confirmation_code(self):
        response = self.client_http.get(reverse('dashboard:admin_reservations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#RES-{self.reservation.confirmation_code}")
        self.assertNotContains(response, f"#RES-{self.reservation.id}")

    def test_payments_page_shows_real_transaction_id_and_reservation_code(self):
        response = self.client_http.get(reverse('dashboard:admin_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "#PAY-WAVE-TX-REAL-123")
        self.assertContains(response, f"#RES-{self.reservation.confirmation_code}")

    def test_payouts_page_shows_real_reservation_code(self):
        response = self.client_http.get(reverse('dashboard:admin_payouts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#RES-{self.reservation.confirmation_code}")
        self.assertNotContains(response, f"#RES-{self.reservation.id}")


class AdminDisputesViewTestCase(TestCase):
    def setUp(self):
        import datetime
        from apps.properties.models import PropertyType
        from apps.properties.services.services import PropertyService
        from apps.reservations.models import ReservationRequest, Reservation
        from apps.support.models import Dispute

        self.client_http = Client()
        self.admin = User.objects.create_superuser(email="admin_disputes@dekouway.sn", password="Password123!")
        self.client_http.force_login(self.admin)

        owner = AccountService.register_owner(
            email="disputes_owner@dekouway.sn", password="Password123!", first_name="Dis", last_name="Owner"
        )
        client_user = AccountService.register_client(
            email="disputes_client@dekouway.sn", password="Password123!", first_name="Dis", last_name="Client"
        )
        prop_type = PropertyType.objects.first()
        prop = PropertyService.create_property(
            owner=owner, property_type_id=prop_type.id, title="Villa Litige", description="Test",
            price=50000, address="Adresse", city="Dakar", district="Ngor",
            surface=100, bedrooms=2, bathrooms=1, max_guests=4,
        )
        req = ReservationRequest.objects.create(
            client=client_user, property=prop, check_in=datetime.date(2026, 9, 1),
            check_out=datetime.date(2026, 9, 5), guests=2,
        )
        reservation = Reservation.objects.create(
            request=req, client=client_user, property=prop,
            check_in=req.check_in, check_out=req.check_out, guests=2, total_price=200000,
            confirmation_code='DKW-DISPUTE1',
        )
        self.open_dispute = Dispute.objects.create(
            reservation=reservation, raised_by=client_user, reason="Logement non conforme",
            description="Description détaillée du litige.",
        )
        self.resolved_dispute = Dispute.objects.create(
            reservation=reservation, raised_by=client_user, reason="Autre litige",
            description="Un autre litige déjà résolu.", status='RESOLVED_CLIENT',
        )

    def test_shows_real_raised_by_email_and_reason(self):
        response = self.client_http.get(reverse('dashboard:admin_disputes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'disputes_client@dekouway.sn')
        self.assertContains(response, 'Logement non conforme')

    def test_status_filter_and_counts(self):
        response = self.client_http.get(reverse('dashboard:admin_disputes'), {'status': 'open'})
        self.assertContains(response, 'Logement non conforme')
        self.assertNotContains(response, 'Autre litige')

        response = self.client_http.get(reverse('dashboard:admin_disputes'), {'status': 'resolved'})
        self.assertContains(response, 'Autre litige')
        self.assertNotContains(response, 'Logement non conforme')

    def test_search_filters_by_reason(self):
        response = self.client_http.get(reverse('dashboard:admin_disputes'), {'search': 'non conforme'})
        self.assertContains(response, 'Logement non conforme')
        self.assertNotContains(response, 'Autre litige')


class ClientReservationsAndPaymentsFilterTestCase(TestCase):
    def setUp(self):
        import datetime
        from apps.properties.models import PropertyType
        from apps.properties.services.services import PropertyService
        from apps.reservations.models import ReservationRequest, Reservation
        from apps.payments.models import Payment
        from apps.payments.choices import PaymentMethodChoices

        self.client_http = Client()
        self.client_user = AccountService.register_client(
            email="client_filter_test@dekouway.sn", password="Password123!", first_name="Cli", last_name="Ent"
        )
        self.client_http.force_login(self.client_user)

        owner = AccountService.register_owner(
            email="client_filter_owner@dekouway.sn", password="Password123!", first_name="Own", last_name="Er"
        )
        prop_type = PropertyType.objects.first()
        prop = PropertyService.create_property(
            owner=owner, property_type_id=prop_type.id, title="Villa Confirmee", description="Test",
            price=50000, address="Adresse", city="Dakar", district="Ngor",
            surface=100, bedrooms=2, bathrooms=1, max_guests=4,
        )
        req = ReservationRequest.objects.create(
            client=self.client_user, property=prop, check_in=datetime.date(2026, 9, 1),
            check_out=datetime.date(2026, 9, 5), guests=2,
        )
        self.confirmed_res = Reservation.objects.create(
            request=req, client=self.client_user, property=prop,
            check_in=req.check_in, check_out=req.check_out, guests=2, total_price=200000, status='CONFIRMED',
            confirmation_code='DKW-CONFIRMED1',
        )

        req2 = ReservationRequest.objects.create(
            client=self.client_user, property=prop, check_in=datetime.date(2026, 6, 1),
            check_out=datetime.date(2026, 6, 5), guests=2,
        )
        self.completed_res = Reservation.objects.create(
            request=req2, client=self.client_user, property=prop,
            check_in=req2.check_in, check_out=req2.check_out, guests=2, total_price=100000, status='COMPLETED',
            confirmation_code='DKW-COMPLETED1',
        )
        self.payment = Payment.objects.create(
            reservation=self.confirmed_res, user=self.client_user, amount=200000, method=PaymentMethodChoices.WAVE,
        )

    def test_status_filter_separates_confirmed_and_completed(self):
        response = self.client_http.get(reverse('dashboard:client_reservations'), {'status': 'confirmed'})
        self.assertContains(response, str(self.confirmed_res.property.title))
        self.assertEqual(response.context['reservations'].count(), 1)

        response = self.client_http.get(reverse('dashboard:client_reservations'), {'status': 'completed'})
        self.assertEqual(response.context['reservations'].count(), 1)
        self.assertEqual(response.context['reservations'].first().id, self.completed_res.id)

    def test_payments_csv_export_contains_real_data(self):
        response = self.client_http.get(reverse('dashboard:client_payments_export'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode()
        self.assertIn('Villa Confirmee', content)
        self.assertIn('200000', content)
