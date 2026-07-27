from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notifications.services.services import NotificationService
from apps.notifications.services.selectors import NotificationSelector
from apps.notifications.api.serializers import NotificationSerializer, NotificationPreferenceSerializer
from apps.notifications.models import NotificationPreference

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API REST de consultation et gestion des notifications In-App.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationSelector.get_user_notifications(self.request.user)

    @action(detail=True, methods=['post'], url_path='read')
    def read(self, request, pk=None):
        notif = self.get_object()
        notif = NotificationService.mark_as_read(notif)
        return Response(NotificationSerializer(notif).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        NotificationService.mark_all_as_read(request.user)
        return Response({'detail': "Toutes les notifications ont été marquées comme lues."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = NotificationSelector.get_unread_count(request.user)
        return Response({'unread_count': count})

    @action(detail=False, methods=['get', 'put'], url_path='preferences')
    def preferences(self, request):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        if request.method == 'PUT':
            serializer = NotificationPreferenceSerializer(pref, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(NotificationPreferenceSerializer(pref).data)
