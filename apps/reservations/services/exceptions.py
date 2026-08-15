class ReservationAlreadyCancelled(Exception):
    """Levée lors d'une tentative d'action sur une réservation déjà annulée."""
    pass

class ReservationAlreadyAccepted(Exception):
    """Levée lors d'une tentative d'action sur une réservation déjà acceptée."""
    pass

class DatesNotAvailable(Exception):
    """Levée lorsque les dates demandées ne sont pas disponibles pour la propriété."""
    pass

class InvalidWorkflowTransition(Exception):
    """Levée lorsqu'une transition de statut de réservation est invalide."""
    pass
