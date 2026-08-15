from rest_framework import serializers
from apps.accounts.models import User, UserProfile, Address, IdentityDocument

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'phone', 'avatar', 'birth_date']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'is_client', 'is_owner', 'is_superadmin', 'is_active', 'is_verified', 'created_at', 'profile']
        read_only_fields = ['id', 'email', 'is_client', 'is_owner', 'is_superadmin', 'is_active', 'is_verified', 'created_at']


class ClientRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)


class OwnerRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    password_confirm = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return attrs


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'postal_code', 'country', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']


class IdentityDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityDocument
        fields = ['id', 'document_type', 'document_number', 'file', 'is_verified', 'verified_at', 'created_at']
        read_only_fields = ['id', 'is_verified', 'verified_at', 'created_at']
