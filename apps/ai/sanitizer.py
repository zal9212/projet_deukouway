import re

class AISanitizer:
    """
    Filtre de sécurité et d'anonymisation (Sanitizer PII) garantissant
    qu'aucune donnée sensible ne soit envoyée vers l'API LLM externe.
    """

    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    PHONE_REGEX = re.compile(r'(\+?\d{1,4}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}')
    CREDIT_CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
    UUID_REGEX = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')

    # Motifs classiques de tentative de manipulation / contournement du prompt système.
    # Détection locale rapide en défense complémentaire des instructions du prompt système
    # (une regex ne peut pas tout attraper, mais bloque gratuitement et sans appel LLM
    # les tentatives les plus fréquentes et évidentes).
    INJECTION_PATTERNS = [
        r"ignor\w*\s+(toutes?\s+)?(les\s+)?(instructions?|consignes?|r[eè]gles?|directives?)",
        r"oubli\w*\s+(toutes?\s+)?(les\s+)?(instructions?|consignes?|r[eè]gles?|directives?)",
        r"(r[eé]v[eè]le|donne|affiche|montre|partage)[\w\s]{0,20}(ton\s+)?(prompt|instructions?|consignes?)\s*(syst[eè]me)?",
        r"tu\s+es\s+(maintenant|d[eé]sormais)\s+",
        r"(fais|fait)\s+comme\s+si\s+tu\s+[eé]tais",
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"you\s+are\s+now\s+",
        r"reveal\s+your\s+(system\s+)?(prompt|instructions?)",
        r"\bsystem\s*prompt\b",
        r"\bjailbreak\b",
        r"\bDAN\s+mode\b",
        r"nouvelles?\s+instructions?\s*:",
        r"new\s+instructions?\s*:",
    ]
    _INJECTION_REGEX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Masque les adresses email, numéros de téléphone, cartes bancaires et UUIDs sensibles.
        """
        if not text:
            return ""

        sanitized = text
        sanitized = cls.EMAIL_REGEX.sub('[EMAIL_MASQUE]', sanitized)
        sanitized = cls.CREDIT_CARD_REGEX.sub('[CARTE_MASQUEE]', sanitized)
        sanitized = cls.PHONE_REGEX.sub('[TELEPHONE_MASQUE]', sanitized)
        sanitized = cls.UUID_REGEX.sub('[ID_ANONYMISE]', sanitized)

        return sanitized

    @classmethod
    def detect_prompt_injection(cls, text: str) -> bool:
        """
        Détection heuristique rapide (sans appel LLM) d'une tentative de manipulation
        du prompt système : instructions cachées demandant à l'IA d'ignorer ses
        consignes, de changer de rôle, ou de révéler son prompt système.
        """
        if not text:
            return False
        return bool(cls._INJECTION_REGEX.search(text))

    @classmethod
    def sanitize_context(cls, context: dict) -> dict:
        """
        Filtre récursivement les dictionnaires de contexte pour supprimer les clés sensibles.
        """
        sensitive_keys = {'password', 'token', 'secret', 'card_number', 'card_cvc', 'phone', 'email', 'ninea'}
        sanitized_ctx = {}

        for k, v in context.items():
            if k.lower() in sensitive_keys:
                continue
            if isinstance(v, str):
                sanitized_ctx[k] = cls.sanitize_text(v)
            elif isinstance(v, dict):
                sanitized_ctx[k] = cls.sanitize_context(v)
            else:
                sanitized_ctx[k] = v

        return sanitized_ctx
