from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_transactional_email(subject: str, recipient_email: str, template_name: str, context: dict) -> bool:
    """
    Envoie un email transactionnel HTML à un destinataire donné.
    """
    try:
        html_message = render_to_string(template_name, context)
        plain_message = f"{subject}\n\nMerci d'utiliser DEKOUWAY."
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@dekouway.sn'),
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=True,
        )
        logger.info(f"Email '{subject}' envoyé avec succès à {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Échec de l'envoi de l'email '{subject}' à {recipient_email} : {e}", exc_info=True)
        return False
