import logging
from typing import List, Dict, Tuple
from apps.accounts.models import User
from apps.ai.prompt_builder import PromptBuilder
from apps.ai.sanitizer import AISanitizer
from apps.ai.services.groq_service import GroqService
from apps.ai.services.platform_context import PlatformContextBuilder
from apps.ai.choices import AIModeChoices

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE = (
    "Je suis l'assistant KYI IMMOBILIER et je ne peux pas suivre ce type de demande. "
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
            system_prompt += "\n\n" + cls._build_admin_context()
        elif getattr(user, 'is_owner', False):
            role_context = "Propriétaire"
            system_prompt = PromptBuilder.get_system_prompt_owner_assistant()
            system_prompt += "\n\n" + cls._build_owner_context(user)

        # Ancrage factuel : le modèle n'a par défaut aucune connaissance du catalogue
        # réel ni des règles de la plateforme. On lui injecte cette "mémoire" à chaque
        # message pour qu'il réponde à partir de données vraies plutôt que d'inventer.
        system_prompt += "\n\n" + PlatformContextBuilder.build()

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

    @classmethod
    def _build_admin_context(cls) -> str:
        from apps.dashboard.services.selectors import DashboardSelector
        s = DashboardSelector.get_admin_stats()
        return (
            "=== DONNÉES OPÉRATIONNELLES RÉELLES DE LA PLATEFORME (utilise ces chiffres, ne les invente jamais) ===\n"
            f"Clients : {s['total_clients']} au total ({s['active_clients']} actifs, {s['blocked_clients']} bloqués, "
            f"{s['new_clients_this_month']} nouveaux ce mois-ci).\n"
            f"Propriétaires : {s['total_owners']} au total ({s['verified_owners']} vérifiés, {s['pending_owners']} en attente de validation KYC).\n"
            f"Logements : {s['total_properties']} au total ({s['published_properties']} publiés, {s['pending_properties']} en attente "
            f"de validation, {s['rejected_properties']} rejetés, {s['suspended_properties']} suspendus).\n"
            f"Réservations : {s['total_reservations']} au total ({s['reservations_today']} aujourd'hui, {s['reservations_this_week']} "
            f"cette semaine, {s['reservations_this_month']} ce mois-ci, {s['reservations_this_year']} cette année).\n"
            f"Volume total encaissé : {s['total_volume']} FCFA. Commission générée : {s['total_revenue']} FCFA. "
            f"Panier moyen : {s['avg_basket']} FCFA.\n"
            f"Reversements : {s['completed_payouts_sum']} FCFA déjà versés aux propriétaires, {s['pending_payouts_sum']} FCFA en attente."
        )

    @classmethod
    def _build_owner_context(cls, user) -> str:
        from apps.dashboard.services.selectors import DashboardSelector
        s = DashboardSelector.get_owner_stats(user.id)
        return (
            "=== VOS DONNÉES PERSONNELLES RÉELLES (utilise ces chiffres, ne les invente jamais) ===\n"
            f"Vos logements : {s['total_properties']} au total ({s['active_properties']} publiés, {s['suspended_properties']} suspendus).\n"
            f"Demandes de réservation en attente de votre réponse : {s['pending_requests']}.\n"
            f"Réservations : {s['confirmed_reservations']} confirmées, {s['cancelled_reservations']} annulées.\n"
            f"Revenus déjà versés : {s['total_payouts']} FCFA au total ({s['monthly_revenue']} FCFA ce mois-ci, "
            f"{s['annual_revenue']} FCFA cette année).\n"
            f"Note moyenne : {s['avg_rating']}/5 sur {s['total_reviews']} avis. Taux d'occupation estimé : {s['occupancy_rate']}%.\n"
            f"Logement le plus réservé : {s['best_property']}. Logement le moins réservé : {s['worst_property']}."
        )
