import json
import logging
from typing import Dict, Any
from apps.ai.sanitizer import AISanitizer
from apps.ai.prompt_builder import PromptBuilder
from apps.ai.services.groq_service import GroqService

logger = logging.getLogger(__name__)

class ModerationService:
    """
    Service d'analyse et modération automatisée du contenu (Spam, Vulgarité, PII Leaks, Contournement).
    """

    @classmethod
    def moderate_text(cls, text: str, user=None) -> Dict[str, Any]:
        """
        Analyse un texte et retourne un dictionnaire récapitulatif du statut de modération.
        """
        if not text:
            return {'flagged': False, 'reason': '', 'categories': []}

        # Étape 1 : Vérification rapide par le Sanitizer Regex local (Protection instantanée)
        has_phone = bool(AISanitizer.PHONE_REGEX.search(text))
        has_email = bool(AISanitizer.EMAIL_REGEX.search(text))
        has_card = bool(AISanitizer.CREDIT_CARD_REGEX.search(text))

        if has_phone or has_email or has_card:
            logger.warning(f"Tentative de fuite PII détectée automatiquement : Phone={has_phone}, Email={has_email}")
            return {
                'flagged': True,
                'reason': "Tentative d'échange de coordonnées personnelles ou de paiement hors plateforme détectée.",
                'categories': ['pii_leak', 'bypass_attempt']
            }

        # Étape 2 : Analyse approfondie par Groq LLM
        messages = [{'role': 'user', 'content': f"Analyse le texte suivant : '{text}'"}]
        llm_reply, is_fallback = GroqService.generate_chat_completion(
            messages=messages,
            system_prompt=PromptBuilder.get_system_prompt_moderation(),
            temperature=0.1,
            user=user,
            feature="MODERATION"
        )

        try:
            result = json.loads(llm_reply)
            return {
                'flagged': bool(result.get('flagged', False)),
                'reason': str(result.get('reason', '')),
                'categories': list(result.get('categories', []))
            }
        except Exception:
            return {
                'flagged': False,
                'reason': "Contenu conforme.",
                'categories': []
            }
