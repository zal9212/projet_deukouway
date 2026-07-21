from django.db.models import QuerySet
from apps.documents.models import Document

class DocumentSelector:
    
    @staticmethod
    def get_pending_documents() -> QuerySet[Document]:
        return Document.objects.filter(is_verified=False, is_deleted=False)
        
    @staticmethod
    def get_user_documents(user_id: str) -> QuerySet[Document]:
        return Document.objects.filter(user_id=user_id, is_deleted=False).order_by('-created_at')
