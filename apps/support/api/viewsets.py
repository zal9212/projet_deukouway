from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.support.services.services import SupportService
from apps.support.services.selectors import SupportSelector
from apps.support.models import SupportCategory
from apps.support.api.serializers import (
    SupportCategorySerializer, TicketSerializer, TicketCreateSerializer, TicketMessageSerializer
)

class SupportCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SupportCategory.objects.filter(is_deleted=False)
    serializer_class = SupportCategorySerializer
    permission_classes = [permissions.AllowAny]


class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    API REST de gestion des tickets d'assistance client et propriétaire.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return SupportSelector.get_all_tickets()
        return SupportSelector.get_user_tickets(user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketSerializer

    def create(self, request, *args, **kwargs):
        serializer = TicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        category = SupportCategory.objects.filter(id=data['category_id']).first()
        if not category:
            return Response({'category_id': ["Catégorie introuvable."]}, status=status.HTTP_404_NOT_FOUND)

        ticket = SupportService.create_ticket(
            user=request.user,
            category=category,
            subject=data['subject'],
            description=data['description']
        )
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='messages')
    def add_message(self, request, pk=None):
        ticket = self.get_object()
        content = request.data.get('content')
        if not content:
            return Response({'content': ["Le contenu du message ne peut pas être vide."]}, status=status.HTTP_400_BAD_REQUEST)

        msg = SupportService.add_message_to_ticket(
            ticket=ticket,
            sender=request.user,
            content=content,
            is_internal=request.data.get('is_internal', False) if getattr(request.user, 'is_superadmin', False) else False
        )
        return Response(TicketMessageSerializer(msg).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        ticket = self.get_object()
        ticket = SupportService.close_ticket(ticket, user=request.user)
        return Response({'detail': "Ticket fermé avec succès.", 'ticket': TicketSerializer(ticket).data})
