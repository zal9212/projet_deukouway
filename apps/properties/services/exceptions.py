class PropertyAlreadyPublished(Exception):
    """Levée lors d'une tentative de publication d'une propriété déjà publiée."""
    pass

class InvalidPropertyStatus(Exception):
    """Levée lorsqu'une propriété passe à un statut invalide."""
    pass

class UnauthorizedPropertyAction(Exception):
    """Levée lorsqu'un utilisateur tente une action sur une propriété qu'il ne possède pas."""
    pass
