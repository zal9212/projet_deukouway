from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Handler d'exceptions centralisé DRF traduisant les exceptions domaine Clean / DDD
    en réponses HTTP REST standardisées et structurées.
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code
        return response

    # Conversion des ValidationErrors Django standard en HTTP 400 Bad Request
    if isinstance(exc, DjangoValidationError):
        data = {
            'detail': exc.message if hasattr(exc, 'message') else str(exc),
            'status_code': status.HTTP_400_BAD_REQUEST
        }
        if hasattr(exc, 'message_dict'):
            data['errors'] = exc.message_dict
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # Capturer les exceptions domaine nommées (UserAlreadyExists, InvalidReservationStatus, etc.)
    exc_class_name = exc.__class__.__name__
    if 'AlreadyExists' in exc_class_name or 'Conflict' in exc_class_name:
        return Response({'detail': str(exc), 'status_code': status.HTTP_409_CONFLICT}, status=status.HTTP_409_CONFLICT)
    elif 'NotFound' in exc_class_name:
        return Response({'detail': str(exc), 'status_code': status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    elif 'Invalid' in exc_class_name or 'Validation' in exc_class_name or 'Exception' in exc_class_name:
        return Response({'detail': str(exc), 'status_code': status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    logger.error(f"Unhandled Exception in API: {exc}", exc_info=True)
    return Response(
        {'detail': "Une erreur interne est survenue sur le serveur.", 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
