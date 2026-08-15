import os
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.views import View

from apps.accounts.models import IdentityDocument


class IdentityDocumentFileView(LoginRequiredMixin, View):
    """
    Sert un fichier de pièce d'identité (recto ou selfie) uniquement au
    propriétaire du document ou à un administrateur. Les fichiers sont
    stockés hors de portée de nginx/du serveur static (voir apps.core.storage) ;
    c'est ici, et uniquement ici, que la permission est vérifiée avant lecture.
    """
    def get(self, request, doc_id, field):
        try:
            doc = IdentityDocument.objects.select_related('user').get(id=doc_id)
        except IdentityDocument.DoesNotExist:
            raise Http404("Document introuvable.")

        user = request.user
        is_owner_of_doc = user.id == doc.user_id
        is_admin = user.is_staff or user.is_superuser or getattr(user, 'is_superadmin', False)
        if not (is_owner_of_doc or is_admin):
            raise PermissionDenied("Vous n'êtes pas autorisé à consulter ce document.")

        if field == 'recto':
            file_field = doc.file
        elif field == 'verso':
            file_field = doc.file_back
        elif field == 'selfie':
            file_field = doc.selfie_file
        else:
            raise Http404("Type de document invalide.")

        if not file_field:
            raise Http404("Fichier introuvable.")

        return FileResponse(file_field.open('rb'), filename=os.path.basename(file_field.name))
