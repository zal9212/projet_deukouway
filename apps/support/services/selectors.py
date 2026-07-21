from django.db.models import QuerySet
from apps.support.models import Ticket

class TicketSelector:
    
    @staticmethod
    def get_open_tickets() -> QuerySet[Ticket]:
        return Ticket.objects.exclude(status='CLOSED').filter(is_deleted=False)
        
    @staticmethod
    def get_user_tickets(user_id: str) -> QuerySet[Ticket]:
        return Ticket.objects.filter(user_id=user_id, is_deleted=False).order_by('-created_at')
