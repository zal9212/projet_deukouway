from django.test import TestCase, override_settings
from apps.ai.services.groq_service import GroqService
from apps.ai.models import AIUsageLog

@override_settings(GROQ_API_KEY='')
class GroqServiceTestCase(TestCase):
    def test_local_fallback_when_no_api_key(self):
        messages = [{'role': 'user', 'content': 'Bonjour, quelles sont vos offres ?'}]
        reply, is_fallback = GroqService.generate_chat_completion(messages, feature="CHAT")
        self.assertTrue(is_fallback)
        self.assertIn("DEKOUWAY", reply)
        self.assertTrue(AIUsageLog.objects.filter(feature="CHAT").exists())

    def test_moderation_fallback_detection(self):
        messages = [{'role': 'user', 'content': 'Appelez-moi au 770000000'}]
        reply, is_fallback = GroqService.generate_chat_completion(messages, feature="MODERATION")
        self.assertTrue(is_fallback)
        self.assertIn("flagged", reply)
