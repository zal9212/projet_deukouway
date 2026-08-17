from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateFileSystemStorage(FileSystemStorage):
    """
    Stockage pour fichiers privés (PII). `FileSystemStorage` retombe sur
    `settings.MEDIA_URL` si `base_url=None` lui est passé au constructeur —
    ça ne suffit donc pas à empêcher un `.url` accidentel dans un template.
    On surcharge `url()` pour échouer bruyamment à la place : tout accès doit
    passer par une vue authentifiée qui vérifie les permissions avant de
    streamer le fichier (voir apps.accounts.views.documents).
    """
    def url(self, name):
        raise NotImplementedError(
            "Ce fichier est privé : utilisez la vue de service authentifiée, jamais .url directement."
        )

    def deconstruct(self):
        # Sans ceci, Django sérialise les migrations avec `location=` résolu en
        # chemin absolu de LA machine où `makemigrations` a tourné (ex. un chemin
        # Windows en dur) — cassant `makemigrations --check` (et la storage
        # elle-même) sur toute autre machine (CI, prod, autre poste). En pointant
        # vers l'instance module-level, le chemin est recalculé à l'exécution,
        # sur chaque machine, via `settings.MEDIA_ROOT`.
        return ('apps.core.storage.private_storage', [], {})


# Stockage privé : les fichiers atterrissent physiquement sous MEDIA_ROOT/private/,
# un chemin que nginx bloque explicitement (voir nginx.conf) et que Django ne sert
# jamais directement via /media/.
private_storage = PrivateFileSystemStorage(
    location=str(settings.MEDIA_ROOT / 'private'),
)
