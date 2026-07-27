from django.test import TestCase, Client, override_settings
from unittest.mock import patch


class MetricsEndpointTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @override_settings(METRICS_TOKEN='')
    def test_denied_when_no_token_configured(self):
        response = self.client.get('/metrics/')
        self.assertEqual(response.status_code, 403)

    @override_settings(METRICS_TOKEN='secret-token-123')
    def test_denied_without_correct_header(self):
        response = self.client.get('/metrics/')
        self.assertEqual(response.status_code, 403)

        response = self.client.get('/metrics/', HTTP_X_METRICS_TOKEN='wrong-token')
        self.assertEqual(response.status_code, 403)

    @override_settings(METRICS_TOKEN='secret-token-123')
    def test_allowed_with_correct_header(self):
        response = self.client.get('/metrics/', HTTP_X_METRICS_TOKEN='secret-token-123')
        self.assertEqual(response.status_code, 200)


class HealthCheckEndpointTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_healthy_response(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')

    def test_db_failure_does_not_leak_exception_details(self):
        with patch('apps.core.views.health.connection') as mock_connection:
            mock_connection.cursor.side_effect = Exception('secret-host db.internal.dekouway:5432 refused connection')
            response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret-host', response.content.decode())
        self.assertNotIn('db.internal.dekouway', response.content.decode())
