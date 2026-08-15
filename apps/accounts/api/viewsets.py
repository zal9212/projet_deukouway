from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from apps.accounts.services.services import AccountService
from apps.accounts.services.selectors import UserSelector
from apps.accounts.api.serializers import (
    UserSerializer, UserProfileSerializer, ClientRegisterSerializer,
    OwnerRegisterSerializer, PasswordChangeSerializer, AddressSerializer,
    IdentityDocumentSerializer
)
from apps.core.api.permissions import IsSuperAdmin

class AuthViewSet(viewsets.GenericViewSet):
    """
    Endpoints REST d'authentification (JWT Register Client/Owner, Password Change, Verification).
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=ClientRegisterSerializer, responses={201: UserSerializer})
    @action(detail=False, methods=['post'], url_path='register-client')
    def register_client(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = AccountService.register_client(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    @extend_schema(request=OwnerRegisterSerializer, responses={201: UserSerializer})
    @action(detail=False, methods=['post'], url_path='register-owner')
    def register_owner(self, request):
        serializer = OwnerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = AccountService.register_owner(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        return Response({
            'detail': "Compte propriétaire créé avec succès. Votre profil est en cours de validation.",
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='logout')
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'detail': "Déconnexion réussie."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'detail': "Jeton invalide ou déjà révoqué."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ["L'ancien mot de passe est incorrect."]}, status=status.HTTP_400_BAD_REQUEST)

        AccountService.change_password(request.user, serializer.validated_data['new_password'])
        return Response({'detail': "Mot de passe mis à jour avec succès."}, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API de consultation et mise à jour du profil utilisateur connecté.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSelector.get_all_active_users().filter(id=self.request.user.id)

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        profile = UserSelector.get_user_profile(request.user)
        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=(request.method == 'PATCH'))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(UserProfileSerializer(profile).data)


class AddressViewSet(viewsets.ModelViewSet):
    """
    CRUD des adresses postales de l'utilisateur.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IdentityDocumentViewSet(viewsets.ModelViewSet):
    """
    API de téléversement et consultation des pièces d'identité (KYC).
    """
    serializer_class = IdentityDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.identity_documents.filter(is_deleted=False)

    def perform_create(self, serializer):
        AccountService.upload_identity_document(
            user=self.request.user,
            document_type=serializer.validated_data['document_type'],
            document_number=serializer.validated_data['document_number'],
            file=serializer.validated_data['file']
        )


class UserManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API d'administration des utilisateurs (SuperAdmin).
    """
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return UserSelector.get_all_users()

    @action(detail=True, methods=['post'], url_path='approve-owner')
    def approve_owner(self, request, pk=None):
        user = self.get_object()
        user = AccountService.approve_owner(user, admin_user=request.user)
        return Response({'detail': f"Propriétaire {user.email} approuvé avec succès.", 'user': UserSerializer(user).data})

    @action(detail=True, methods=['post'], url_path='block')
    def block(self, request, pk=None):
        user = self.get_object()
        user = AccountService.block_user(user, admin_user=request.user)
        return Response({'detail': f"Utilisateur {user.email} bloqué.", 'user': UserSerializer(user).data})

    @action(detail=True, methods=['post'], url_path='unblock')
    def unblock(self, request, pk=None):
        user = self.get_object()
        user = AccountService.unblock_user(user, admin_user=request.user)
        return Response({'detail': f"Utilisateur {user.email} débloqué.", 'user': UserSerializer(user).data})
