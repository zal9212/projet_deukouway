from rest_framework import serializers
from apps.documents.models import DocumentCategory, Document, DocumentVerification

class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'slug']


class DocumentSerializer(serializers.ModelSerializer):
    category = DocumentCategorySerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'user_email', 'category', 'title', 'file', 'is_verified', 'created_at']
        read_only_fields = ['id', 'user_email', 'is_verified', 'created_at']


class DocumentUploadSerializer(serializers.Serializer):
    category_id = serializers.UUIDField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    file = serializers.FileField(required=True)
