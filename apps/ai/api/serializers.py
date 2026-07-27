from rest_framework import serializers
from apps.ai.models import Conversation, ConversationMessage, AIUsageLog

class ConversationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessage
        fields = ['id', 'role', 'content', 'tokens_used', 'latency_ms', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = ConversationMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'mode', 'title', 'messages', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, min_length=1)
    mode = serializers.CharField(required=False, default='GENERAL_CHAT')


class RecommendationRequestSerializer(serializers.Serializer):
    city = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    guests = serializers.IntegerField(required=False, default=1)


class ModerationRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, min_length=1)


class SummaryRequestSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)


class DescriptionGenRequestSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    property_type = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    district = serializers.CharField(required=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    surface = serializers.IntegerField(required=True, min_value=1)
    bedrooms = serializers.IntegerField(required=True, min_value=0)
    bathrooms = serializers.IntegerField(required=True, min_value=0)
    equipments = serializers.CharField(required=False, allow_blank=True)
