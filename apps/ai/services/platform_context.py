from django.conf import settings
from django.core.cache import cache
from apps.properties.services.selectors import PropertySelector
from apps.payments.services.selectors import PaymentSelector

PLATFORM_CONTEXT_CACHE_KEY = 'ai_platform_context'
MAX_PROPERTIES_IN_CONTEXT = 100


class PlatformContextBuilder:
    """
    Construit un résumé factuel et compact de la plateforme (logements publiés,
    règles financières, parcours de réservation) à injecter dans le prompt
    système du chatbot IA, pour qu'il réponde à partir de données réelles
    plutôt que d'inventer des logements ou des tarifs qui n'existent pas.

    Mis en cache 5 minutes : le catalogue évolue en continu (nouvelles
    annonces, changements de statut) donc pas de cache long comme pour
    PlatformSettings, mais on évite de reconstruire ce bloc à chaque message.
    """

    @classmethod
    def build(cls) -> str:
        if settings.TESTING:
            return cls._build_fresh()
        cached = cache.get(PLATFORM_CONTEXT_CACHE_KEY)
        if cached is not None:
            return cached
        context = cls._build_fresh()
        cache.set(PLATFORM_CONTEXT_CACHE_KEY, context, timeout=300)
        return context

    @classmethod
    def _build_fresh(cls) -> str:
        platform_settings = PaymentSelector.get_platform_settings()
        published = PropertySelector.get_published_properties()
        total_count = published.count()
        properties = published[:MAX_PROPERTIES_IN_CONTEXT]

        lines = [
            "=== DONNÉES RÉELLES DE LA PLATEFORME (à utiliser pour répondre — ne jamais inventer d'autres logements, tarifs ou informations) ===",
            f"Nom de la plateforme : {platform_settings.site_name}",
            f"Commission plateforme par défaut : {platform_settings.commission_percentage}% (peut être personnalisée pour certains logements)",
            f"Frais de service client (fixe, en plus du prix du logement) : {platform_settings.client_service_fee} FCFA par réservation",
            "Moyens de paiement acceptés : Wave, Orange Money, Carte bancaire.",
            "Parcours de réservation : le client envoie une demande -> le SuperAdmin vérifie la disponibilité et transmet le "
            "lien de paiement -> le client règle le montant complet -> le SuperAdmin met le client en contact avec le "
            "propriétaire pour l'arrivée.",
            "",
        ]

        if total_count == 0:
            lines.append("Logements actuellement publiés sur la plateforme : aucun pour le moment.")
        else:
            header = f"Logements actuellement publiés sur la plateforme ({total_count} au total"
            header += f", les {MAX_PROPERTIES_IN_CONTEXT} plus récents listés ci-dessous" if total_count > MAX_PROPERTIES_IN_CONTEXT else ""
            header += ") :"
            lines.append(header)
            for p in properties:
                period_label = 'mois' if p.pricing_period == 'MONTHLY' else 'nuit'
                type_label = f"{p.property_type.category.name} - {p.property_type.name}" if p.property_type else "Type non précisé"
                lines.append(
                    f"- {p.title} | {type_label} | {p.district}, {p.city} | {p.price} FCFA/{period_label} "
                    f"| {p.bedrooms} ch. / {p.bathrooms} sdb. | jusqu'à {p.max_guests} pers. | {p.surface} m²"
                )

        lines.append("")
        lines.append(
            "Utilise UNIQUEMENT les logements listés ci-dessus pour répondre aux questions sur la disponibilité, les prix "
            "ou les caractéristiques des biens. Si rien ne correspond à la demande, dis-le clairement et propose "
            "l'alternative la plus proche dans la liste, plutôt que d'inventer un logement qui n'existe pas."
        )

        return "\n".join(lines)
