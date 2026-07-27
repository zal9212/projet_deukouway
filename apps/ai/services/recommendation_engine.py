from typing import List, Dict, Any
from apps.properties.services.selectors import PropertySelector
from apps.ai.prompt_builder import PromptBuilder
from apps.ai.services.groq_service import GroqService

class RecommendationEngine:
    """
    Moteur de recommandation intelligente et de suggestions de repli (Smart Fallbacks).
    """

    @classmethod
    def get_recommendations(
        cls,
        user=None,
        city: str = None,
        district: str = None,
        min_price: float = None,
        max_price: float = None,
        guests: int = 1
    ) -> Dict[str, Any]:
        """
        Recommande des logements ou formule des suggestions intelligentes en cas d'absence de résultat direct.
        """
        # Recherche directe via PropertySelector
        direct_properties = PropertySelector.search_properties(
            city=city,
            district=district,
            min_price=min_price,
            max_price=max_price
        )

        if direct_properties.exists():
            return {
                'has_direct_matches': True,
                'count': direct_properties.count(),
                'properties_ids': [str(p.id) for p in direct_properties[:6]],
                'suggestions': []
            }

        # Si 0 résultat direct -> suggestions intelligentes de repli (Smart Fallback)
        fallback_properties = PropertySelector.search_properties(city=city)
        if not fallback_properties.exists():
            fallback_properties = PropertySelector.get_featured_properties(limit=6)

        user_prompt = f"La recherche pour Ville={city}, Quartier={district}, Prix Max={max_price} n'a donné aucun résultat direct."
        ai_suggestion, _ = GroqService.generate_chat_completion(
            messages=[{'role': 'user', 'content': user_prompt}],
            system_prompt=PromptBuilder.get_system_prompt_recommendation(),
            user=user,
            feature="RECOMMENDATION"
        )

        return {
            'has_direct_matches': False,
            'count': 0,
            'suggested_properties_ids': [str(p.id) for p in fallback_properties[:6]],
            'ai_advice': ai_suggestion or "Nous vous suggérons d'élargir légèrement votre budget ou d'explorer les quartiers environnants."
        }
