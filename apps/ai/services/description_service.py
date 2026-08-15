from typing import Dict, Any
from apps.ai.prompt_builder import PromptBuilder
from apps.ai.services.groq_service import GroqService

class DescriptionService:
    """
    Service de génération automatique de descriptions immobilières valorisantes et de résumés synthétiques.
    """

    @classmethod
    def generate_property_description(
        cls,
        title: str,
        property_type: str,
        city: str,
        district: str,
        price: float,
        surface: int,
        bedrooms: int,
        bathrooms: int,
        equipments: str = "",
        user=None
    ) -> Dict[str, Any]:
        """
        Rédige un titre, une description professionnelle et la liste des points forts.
        """
        user_prompt = (
            f"Titre d'origine: {title}\n"
            f"Type: {property_type}, Ville: {city}, Quartier: {district}\n"
            f"Prix par nuit: {price} XOF, Surface: {surface} m²\n"
            f"Chambres: {bedrooms}, Salles de bain: {bathrooms}\n"
            f"Équipements: {equipments}"
        )

        reply_content, _ = GroqService.generate_chat_completion(
            messages=[{'role': 'user', 'content': user_prompt}],
            system_prompt=PromptBuilder.get_system_prompt_description_gen(),
            user=user,
            feature="DESCRIPTION"
        )

        return {
            'generated_title': f"{property_type} de standing à {district}, {city}",
            'generated_description': reply_content,
            'highlights': [
                f"{bedrooms} chambre(s) spacieuse(s)",
                f"Surface généreuse de {surface} m²",
                f"Emplacement prisé à {district}, {city}"
            ]
        }

    @classmethod
    def generate_summary(cls, title: str, description: str, user=None) -> str:
        """
        Génère un résumé concis (1-2 phrases) pour les cartes de présentation de logements.
        """
        user_prompt = f"Résume cette annonce en 2 phrases captivantes : Titre='{title}', Description='{description}'"
        summary, _ = GroqService.generate_chat_completion(
            messages=[{'role': 'user', 'content': user_prompt}],
            system_prompt="Tu es un rédacteur immobilier. Génère un résumé synthétique de 2 phrases maximum.",
            max_tokens=150,
            user=user,
            feature="SUMMARY"
        )
        return summary
