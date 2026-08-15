class DocumentNotVerified(Exception):
    """Levée lorsqu'une action requiert un document vérifié."""
    pass

class DocumentAlreadyVerified(Exception):
    """Levée lors d'une tentative de vérifier un document déjà vérifié."""
    pass
