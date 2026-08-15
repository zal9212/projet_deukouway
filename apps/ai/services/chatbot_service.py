import logging
from typing import List, Dict, Tuple
from apps.accounts.models import User
from apps.ai.prompt_builder import PromptBuilder
from apps.ai.sanitizer import AISanitizer
from apps.ai.services.groq_service import GroqService
from apps.ai.choices import AIModeChoices

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE = (
    "Je suis l'assistant DEKOUWAY et je ne peux pas suivre ce type de demande. "
    "Je peux en revanche vous aider pour tout ce qui concerne les logements, "
    "les réservations ou les paiements sur la plateforme. Que puis-je faire pour vous ?"
)

class ChatbotService:
    """
    Moteur conversationnel intelligent orienté rôle (Client, Propriétaire, SuperAdmin ERP).
    """

    @classmethod
    def ask_chatbot(
        cls,
        user: User,
        message: str,
        history: List[Dict[str, str]] = None,
        mode: str = AIModeChoices.GENERAL_CHAT
    ) -> Tuple[str, bool]:
        """
        Traite un message utilisateur et génère la réponse contextuelle via Groq.
        """
        if AISanitizer.detect_prompt_injection(message):
            logger.warning(
                f"Tentative de manipulation du prompt détectée (user={getattr(user, 'email', 'anonyme')}): {message[:200]!r}"
            )
            return REFUSAL_MESSAGE, False

        role_context = "Client"
        system_prompt = PromptBuilder.get_system_prompt_chatbot(role_context)

        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            role_context = "SuperAdmin"
            system_prompt = PromptBuilder.get_system_prompt_erp_admin()
        elif getattr(user, 'is_owner', False):
            role_context = "Propriétaire"
            system_prompt = PromptBuilder.get_system_prompt_owner_assistant()

        messages_payload = []
        if history:
            messages_payload.extend(history)
            
        messages_payload.append({'role': 'user', 'content': message})

        reply, is_fallback = GroqService.generate_chat_completion(
            messages=messages_payload,
            system_prompt=system_prompt,
            user=user,
            feature="CHAT"
        )
        return reply, is_fallback
