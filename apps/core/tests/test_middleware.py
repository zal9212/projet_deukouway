from django.test import TestCase, Client
from django.core.cache import cache
from django.urls import reverse


class RateLimitMiddlewareTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.url = reverse('public:contact')

    def _post(self, **extra):
        return self.client.post(self.url, {
            'name': 'Test', 'email': 'ratelimit@test.com', 'subject': 'Sujet', 'message': 'Message de test.',
        }, **extra)

    def test_blocks_after_limit_exceeded(self):
        for _ in range(5):
            response = self._post()
            self.assertNotEqual(response.status_code, 403)
        response = self._post()
        self.assertEqual(response.status_code, 403)

    def test_spoofed_first_hop_does_not_bypass_limit(self):
        # nginx appends the real client IP as the LAST entry of X-Forwarded-For;
        # anything before that is attacker-supplied and must be ignored.
        for i in range(5):
            response = self._post(HTTP_X_FORWARDED_FOR=f'1.2.3.{i}, 9.9.9.9')
            self.assertNotEqual(response.status_code, 403)
        response = self._post(HTTP_X_FORWARDED_FOR='1.2.3.99, 9.9.9.9')
        self.assertEqual(response.status_code, 403)

    def test_different_real_ip_is_not_blocked(self):
        for _ in range(5):
            self._post(HTTP_X_FORWARDED_FOR='5.5.5.5, 1.1.1.1')
        response = self._post(HTTP_X_FORWARDED_FOR='5.5.5.5, 2.2.2.2')
        self.assertNotEqual(response.status_code, 403)
