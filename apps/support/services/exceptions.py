class TicketAlreadyClosed(Exception):
    """Levée lors d'une tentative d'action sur un ticket déjà fermé."""
    pass

class UnauthorizedTicketAction(Exception):
    """Levée lorsqu'un utilisateur tente de modifier un ticket qui ne lui appartient pas."""
    pass
