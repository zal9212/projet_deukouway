class PaymentAlreadyCompleted(Exception):
    """Levée lors d'une tentative de paiement d'une réservation déjà payée."""
    pass

class InvalidAmount(Exception):
    """Levée lorsqu'un montant invalide est fourni."""
    pass

class PayoutAlreadyProcessed(Exception):
    """Levée lorsqu'un reversement est déjà terminé ou en cours de traitement."""
    pass

class CompletedPaymentNotFound(Exception):
    """Levée lorsqu'aucun paiement au statut SUCCESS n'existe pour la réservation."""
    pass

class CommissionNotCalculated(Exception):
    """Levée lorsqu'un reversement est demandé avant que la commission n'ait été calculée."""
    pass

class InvalidPaymentState(Exception):
    """Levée lors d'une opération (ex: remboursement) invalide pour le statut actuel du paiement."""
    pass
