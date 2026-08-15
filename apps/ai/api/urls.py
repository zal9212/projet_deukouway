from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai.api.viewsets import (
    ChatViewSet, RecommendationViewSet, ModerationViewSet,
    SummaryViewSet, DescriptionGenViewSet, ConversationHistoryViewSet
)

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='ai-chat')
router.register(r'recommendations', RecommendationViewSet, basename='ai-recommendations')
router.register(r'moderation', ModerationViewSet, basename='ai-moderation')
router.register(r'summary', SummaryViewSet, basename='ai-summary')
router.register(r'description', DescriptionGenViewSet, basename='ai-description')
router.register(r'history', ConversationHistoryViewSet, basename='ai-history')

urlpatterns = [
    path('', include(router.urls)),
]
