from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.core.forms import validate_max_file_size, validate_allowed_file_extensions, validate_file_content_type
from apps.documents.models import Document, DocumentCategory, DocumentVerification
from apps.documents.services.exceptions import DocumentAlreadyVerified
import logging

logger = logging.getLogger(__name__)

ALLOWED_DOCUMENT_EXTENSIONS = ('pdf', 'jpg', 'jpeg', 'png', 'docx')

class DocumentService:

    @staticmethod
    @transaction.atomic
    def upload(user: User, category: DocumentCategory, title: str, file) -> Document:
        # Ces validateurs sont déjà déclarés sur le modèle mais Django ne les
        # applique jamais sur un simple .create() : on les appelle explicitement
        # ici pour qu'un fichier non autorisé (extension ou contenu réel) soit
        # rejeté avant tout enregistrement, quel que soit l'appelant.
        validate_allowed_file_extensions(file, ALLOWED_DOCUMENT_EXTENSIONS)
        validate_file_content_type(file, ALLOWED_DOCUMENT_EXTENSIONS)
        validate_max_file_size(file, max_size_mb=10.0)

        doc = Document.objects.create(
            user=user,
            category=category,
            title=title,
            file=file,
            is_verified=False
        )
        logger.info(f"Document téléchargé : {doc.id} par {user.email}")
        return doc

    @staticmethod
    @transaction.atomic
    def delete(document: Document, user: User) -> None:
        if document.user_id != user.id:
            raise Exception("Non autorisé à supprimer ce document.")
        document.soft_delete()
        logger.info(f"Document supprimé logiquement : {document.id} par {user.email}")

    @staticmethod
    @transaction.atomic
    def validate_document(document: Document, admin_user: User, notes: str = "") -> DocumentVerification:
        if document.is_verified:
            raise DocumentAlreadyVerified("Le document est déjà vérifié.")
            
        document.is_verified = True
        document.save(update_fields=['is_verified'])
        
        verification = DocumentVerification.objects.create(
            document=document,
            verified_by=admin_user,
            status='APPROVED',
            notes=notes
        )
        logger.info(f"Document {document.id} vérifié par {admin_user.email}")
        return verification

    @staticmethod
    @transaction.atomic
    def reject_document(document: Document, admin_user: User, notes: str) -> DocumentVerification:
        if document.is_verified:
            raise DocumentAlreadyVerified("Impossible de rejeter un document déjà vérifié.")
            
        verification = DocumentVerification.objects.create(
            document=document,
            verified_by=admin_user,
            status='REJECTED',
            notes=notes
        )
        logger.warning(f"Document {document.id} rejeté par {admin_user.email} : {notes}")
        return verification

    @staticmethod
    def generate_pdf(context: dict, template_path: str) -> bytes:
        """
        Génération d'un document PDF.
        (Espace réservé pour ReportLab ou WeasyPrint).
        """
        logger.info("Génération de PDF déclenchée")
        return b"%PDF-1.4 Fake PDF content"

    @staticmethod
    @transaction.atomic
    def archive(document: Document) -> Document:
        # Logique métier pour archiver un document
        logger.info(f"Document archivé : {document.id}")
        return document

    @staticmethod
    @transaction.atomic
    def restore(document: Document) -> Document:
        document.restore()
        logger.info(f"Document restauré : {document.id}")
        return document
