class PaymentAlreadyCompleted(Exception):
    """Levée lors d'une tentative de paiement d'une réservation déjà payée."""
    pass

class InvalidAmount(Exception):
    """Levée lorsqu'un montant invalide est fourni."""
    pass

class PayoutAlreadyProcessed(Exception):
    """Levée lorsqu'un reversement est déjà terminé ou en cours de traitement."""
    pass
