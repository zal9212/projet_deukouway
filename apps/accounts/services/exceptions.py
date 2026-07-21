class UserAlreadyExists(Exception):
    """Levée lors d'une tentative d'inscription avec un email déjà existant."""
    pass

class InvalidRoleException(Exception):
    """Levée lors d'une tentative d'attribution d'un rôle invalide à un utilisateur."""
    pass

class OwnerNotVerified(Exception):
    """Levée lorsqu'une action requiert le statut de propriétaire vérifié."""
    pass

class InvalidWorkflowTransition(Exception):
    """Levée lorsqu'une transition de statut n'est pas autorisée."""
    pass
