from django.db.models import QuerySet, Q
from apps.documents.models import Document, DocumentCategory

class DocumentSelector:

    @staticmethod
    def get_pending_documents() -> QuerySet[Document]:
        return Document.objects.filter(is_verified=False, is_deleted=False).select_related('user').order_by('-created_at')

    @staticmethod
    def get_user_documents(user_id: str) -> QuerySet[Document]:
        return Document.objects.filter(user_id=user_id, is_deleted=False).select_related('category').order_by('-created_at')

    @staticmethod
    def get_all_documents(search_query: str = None, category: str = None) -> QuerySet[Document]:
        qs = Document.objects.filter(is_deleted=False).select_related('user', 'category').order_by('-created_at')
        if search_query:
            qs = qs.filter(Q(title__icontains=search_query) | Q(user__email__icontains=search_query))
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    @staticmethod
    def get_all_categories() -> QuerySet[DocumentCategory]:
        return DocumentCategory.objects.filter(is_deleted=False).order_by('name')
