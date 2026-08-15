from django.db.models import QuerySet, Q
from apps.support.models import Ticket, Dispute, SupportCategory, ContactMessage

class TicketSelector:

    @staticmethod
    def get_contact_messages() -> QuerySet[ContactMessage]:
        return ContactMessage.objects.filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_open_tickets() -> QuerySet[Ticket]:
        return Ticket.objects.exclude(status='CLOSED').filter(is_deleted=False).select_related('user', 'category').order_by('-created_at')
        
    @staticmethod
    def get_user_tickets(user_id: str) -> QuerySet[Ticket]:
        return Ticket.objects.filter(user_id=user_id, is_deleted=False).select_related('category').order_by('-created_at')

    @staticmethod
    def get_all_tickets() -> QuerySet[Ticket]:
        return Ticket.objects.filter(is_deleted=False).select_related('user', 'category').order_by('-created_at')

    @staticmethod
    def get_ticket_by_id(ticket_id: str) -> Ticket:
        return Ticket.objects.select_related('user', 'category').prefetch_related('messages__sender').get(id=ticket_id, is_deleted=False)

    @staticmethod
    def get_disputes(search_query: str = None, status: str = None) -> QuerySet[Dispute]:
        qs = Dispute.objects.filter(is_deleted=False).select_related('reservation', 'raised_by').order_by('-created_at')
        if search_query:
            qs = qs.filter(
                Q(reason__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(raised_by__email__icontains=search_query)
            )
        if status == 'open':
            qs = qs.exclude(status__in=['RESOLVED_CLIENT', 'RESOLVED_OWNER', 'RESOLVED_SPLIT'])
        elif status == 'resolved':
            qs = qs.filter(status__in=['RESOLVED_CLIENT', 'RESOLVED_OWNER', 'RESOLVED_SPLIT'])
        return qs

    @staticmethod
    def get_categories() -> QuerySet[SupportCategory]:
        return SupportCategory.objects.filter(is_deleted=False)

# Alias pour cohérence avec les ViewSets
SupportSelector = TicketSelector
