from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.ai.services.chatbot_service import ChatbotService
from apps.ai.services.recommendation_engine import RecommendationEngine
from apps.ai.services.moderation_service import ModerationService
from apps.ai.services.description_service import DescriptionService
from apps.ai.services.conversation_service import ConversationService
from apps.ai.selectors.selectors import AIConversationSelector
from apps.ai.api.serializers import (
    ChatRequestSerializer, RecommendationRequestSerializer, ModerationRequestSerializer,
    SummaryRequestSerializer, DescriptionGenRequestSerializer, ConversationSerializer
)

class ChatViewSet(viewsets.ViewSet):
    """
    API REST du Chatbot conversationnel DEKOUWAY (Groq LLM).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ChatRequestSerializer)
    def create(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        conv = ConversationService.get_or_create_conversation(request.user, mode=data.get('mode', 'GENERAL_CHAT'))
        ConversationService.record_message(conv, role='USER', content=data['message'])

        history = [{'role': m.role.lower(), 'content': m.content} for m in conv.messages.all()]
        reply, is_fallback = ChatbotService.ask_chatbot(request.user, message=data['message'], history=history, mode=data.get('mode'))

        ConversationService.record_message(conv, role='ASSISTANT', content=reply)

        return Response({
            'conversation_id': str(conv.id),
            'reply': reply,
            'fallback_used': is_fallback
        }, status=status.HTTP_200_OK)


class RecommendationViewSet(viewsets.ViewSet):
    """
    API REST de recommandations intelligentes et suggestions de repli.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RecommendationRequestSerializer)
    def create(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        res = RecommendationEngine.get_recommendations(
            user=request.user if request.user and request.user.is_authenticated else None,
            city=data.get('city'),
            district=data.get('district'),
            min_price=float(data['min_price']) if data.get('min_price') else None,
            max_price=float(data['max_price']) if data.get('max_price') else None,
            guests=data.get('guests', 1)
        )
        return Response(res, status=status.HTTP_200_OK)


class ModerationViewSet(viewsets.ViewSet):
    """
    API REST de modération automatique du contenu.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ModerationRequestSerializer)
    def create(self, request):
        serializer = ModerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        res = ModerationService.moderate_text(serializer.validated_data['text'], user=request.user)
        return Response(res, status=status.HTTP_200_OK)


class SummaryViewSet(viewsets.ViewSet):
    """
    API REST de génération de résumé synthétique de logement.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=SummaryRequestSerializer)
    def create(self, request):
        serializer = SummaryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        summary = DescriptionService.generate_summary(title=data['title'], description=data['description'], user=request.user)
        return Response({'summary': summary}, status=status.HTTP_200_OK)


class DescriptionGenViewSet(viewsets.ViewSet):
    """
    API REST de génération automatique de description d'annonce pour le propriétaire.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=DescriptionGenRequestSerializer)
    def create(self, request):
        serializer = DescriptionGenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        res = DescriptionService.generate_property_description(
            title=data['title'],
            property_type=data['property_type'],
            city=data['city'],
            district=data['district'],
            price=float(data['price']),
            surface=data['surface'],
            bedrooms=data['bedrooms'],
            bathrooms=data['bathrooms'],
            equipments=data.get('equipments', ''),
            user=request.user
        )
        return Response(res, status=status.HTTP_200_OK)


class ConversationHistoryViewSet(viewsets.ModelViewSet):
    """
    API REST de consultation et suppression de l'historique de conversation IA.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIConversationSelector.get_user_conversations(self.request.user.id)

    @action(detail=False, methods=['delete'], url_path='clear')
    def clear(self, request):
        ConversationService.clear_user_history(request.user)
        return Response({'detail': "Historique des conversations effacé avec succès."}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        ConversationService.clear_user_history(request.user)
        return Response({'detail': "Historique des conversations effacé avec succès."}, status=status.HTTP_204_NO_CONTENT)
