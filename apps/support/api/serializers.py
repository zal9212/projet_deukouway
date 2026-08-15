from rest_framework import serializers
from apps.support.models import SupportCategory, Ticket, TicketMessage

class SupportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportCategory
        fields = ['id', 'name', 'slug', 'description']


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source='sender.email', read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'sender_email', 'content', 'is_internal', 'created_at']
        read_only_fields = ['id', 'sender_email', 'is_internal', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    category = SupportCategorySerializer(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'user_email', 'category', 'subject', 'description', 'status', 'messages', 'created_at']
        read_only_fields = ['id', 'user_email', 'status', 'created_at']


class TicketCreateSerializer(serializers.Serializer):
    category_id = serializers.UUIDField(required=True)
    subject = serializers.CharField(max_length=255, required=True, min_length=5)
    description = serializers.CharField(required=True, min_length=15)
