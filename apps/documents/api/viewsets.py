from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.documents.services.services import DocumentService
from apps.documents.services.selectors import DocumentSelector
from apps.documents.models import DocumentCategory, Document
from apps.documents.api.serializers import (
    DocumentSerializer, DocumentUploadSerializer, DocumentCategorySerializer
)
from apps.core.api.permissions import IsSuperAdmin

class DocumentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentCategory.objects.filter(is_deleted=False)
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.AllowAny]


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API REST de gestion et validation des documents légaux et justificatifs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_superuser:
            return DocumentSelector.get_all_documents()
        return DocumentSelector.get_user_documents(user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    def create(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        category = DocumentCategory.objects.filter(id=data['category_id']).first()
        if not category:
            return Response({'category_id': ["Catégorie introuvable."]}, status=status.HTTP_404_NOT_FOUND)

        doc = DocumentService.upload(
            user=request.user,
            category=category,
            title=data['title'],
            file=data['file']
        )
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin], url_path='verify')
    def verify(self, request, pk=None):
        doc = self.get_object()
        verification = DocumentService.validate_document(doc, admin_user=request.user)
        return Response({'detail': "Document vérifié et approuvé.", 'document': DocumentSerializer(doc).data})

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin], url_path='reject')
    def reject(self, request, pk=None):
        doc = self.get_object()
        reason = request.data.get('reason', 'Document non conforme')
        verification = DocumentService.reject_document(doc, admin_user=request.user, notes=reason)
        return Response({'detail': "Document rejeté.", 'document': DocumentSerializer(doc).data})
