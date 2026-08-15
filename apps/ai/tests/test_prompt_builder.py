from django.test import TestCase
from apps.ai.prompt_builder import PromptBuilder

class PromptBuilderTestCase(TestCase):
    def test_prompt_builder_returns_non_empty_strings(self):
        chatbot_prompt = PromptBuilder.get_system_prompt_chatbot("Client")
        self.assertIn("DEKOUWAY", chatbot_prompt)
        self.assertIn("Client", chatbot_prompt)

        erp_prompt = PromptBuilder.get_system_prompt_erp_admin()
        self.assertIn("SuperAdmin", erp_prompt)

        owner_prompt = PromptBuilder.get_system_prompt_owner_assistant()
        self.assertIn("Propriétaire", owner_prompt)

        mod_prompt = PromptBuilder.get_system_prompt_moderation()
        self.assertIn("modération", mod_prompt.lower())

        desc_prompt = PromptBuilder.get_system_prompt_description_gen()
        self.assertIn("rédaction", desc_prompt.lower())
