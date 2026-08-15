import time
import logging
from typing import List, Dict, Tuple
from django.conf import settings

from apps.ai.sanitizer import AISanitizer
from apps.ai.models import AIUsageLog

logger = logging.getLogger(__name__)

class GroqService:
    """
    Client de service centralisé pour l'API Groq LLM.
    Gère les timeouts, retries, l'anonymisation PII, la journalisation des jetons
    et le basculement automatique sur un moteur de secours local (Fallback).
    """

    @classmethod
    def generate_chat_completion(
        cls,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user=None,
        feature: str = "CHAT"
    ) -> Tuple[str, bool]:
        """
        Génère une réponse LLM via Groq API.
        Retourne un tuple (contenu_réponse, est_fallback_utilisé).
        """
        selected_model = model or getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        timeout = getattr(settings, 'GROQ_TIMEOUT', 10.0)

        # Assainissement des messages d'entrée (PII Sanitizer)
        sanitized_messages = []
        if system_prompt:
            sanitized_messages.append({'role': 'system', 'content': AISanitizer.sanitize_text(system_prompt)})
        
        for msg in messages:
            sanitized_messages.append({
                'role': msg['role'],
                'content': AISanitizer.sanitize_text(msg['content'])
            })

        start_time = time.time()

        # Si pas de clé d'API configurée, basculer immédiatement sur le moteur de secours (Fallback)
        if not api_key:
            logger.info("Clé API Groq non configurée. Basculement sur le moteur de secours local.")
            fallback_response = cls._local_fallback(sanitized_messages, feature)
            cls._log_usage(user, feature, selected_model, 0, 0, 0, time.time() - start_time, True, True)
            return fallback_response, True

        try:
            from groq import Groq
            client = Groq(api_key=api_key, timeout=timeout)
            
            response = client.chat.completions.create(
                messages=sanitized_messages,
                model=selected_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            execution_time = time.time() - start_time
            reply_content = response.choices[0].message.content or ""
            
            prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') else 0
            completion_tokens = getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') else 0
            total_tokens = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0

            cls._log_usage(user, feature, selected_model, prompt_tokens, completion_tokens, total_tokens, execution_time, True, False)
            return reply_content, False

        except Exception as e:
            execution_time = time.time() - start_time
            logger.warning(f"Échec de l'appel à Groq API ({e}). Utilisation du fallback local.")
            fallback_response = cls._local_fallback(sanitized_messages, feature)
            cls._log_usage(user, feature, selected_model, 0, 0, 0, execution_time, False, True)
            return fallback_response, True

    @classmethod
    def _local_fallback(cls, messages: List[Dict[str, str]], feature: str) -> str:
        """
        Moteur de secours local garantissant qu'aucune requête ne plante en cas d'indisponibilité du LLM.
        """
        last_user_msg = messages[-1]['content'] if messages else ""

        if feature == "MODERATION":
            # Modération algorithmique basée sur Regex
            has_forbidden = bool(AISanitizer.PHONE_REGEX.search(last_user_msg) or AISanitizer.EMAIL_REGEX.search(last_user_msg))
            return f'{{"flagged": {str(has_forbidden).lower()}, "reason": "Détection automatique par filtre de sécurité local", "categories": ["pii_leak"]}}'
            
        elif feature == "DESCRIPTION":
            return "Superbe bien disponible sur DEKOUWAY. Confort exceptionnel, emplacement privilégié et équipements modernes. Idéal pour votre séjour."
            
        elif feature == "SUMMARY":
            return "Logement confortable et idéalement situé pour vos séjours sur la plateforme DEKOUWAY."

        return (
            "Bienvenue sur DEKOUWAY ! Notre assistant enregistre actuellement votre demande. "
            "Rappelez-vous que sur DEKOUWAY, toutes vos réservations et paiements sont 100% sécurisés. "
            "Comment puis-je vous aider pour votre séjour ?"
        )

    @classmethod
    def _log_usage(cls, user, feature: str, model_name: str, p_tokens: int, c_tokens: int, t_tokens: int, exec_time: float, success: bool, fallback: bool):
        try:
            target_user = user if (user and hasattr(user, 'is_authenticated') and user.is_authenticated) else None
            AIUsageLog.objects.create(
                user=target_user,
                feature=feature,
                model_name=model_name,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                execution_time_sec=exec_time,
                is_success=success,
                fallback_used=fallback
            )
        except Exception as e:
            logger.error(f"Erreur lors de la journalisation d'usage IA: {e}")
