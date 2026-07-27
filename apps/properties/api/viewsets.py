from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema

from apps.properties.services.selectors import PropertySelector
from apps.properties.services.services import PropertyService
from apps.properties.models import PropertyCategory, PropertyType, PropertyFavorite
from apps.properties.api.serializers import (
    PropertyListSerializer, PropertyDetailSerializer, PropertyCreateUpdateSerializer,
    PropertyCategorySerializer, PropertyTypeSerializer, PropertyFavoriteSerializer
)
from apps.properties.api.filters import PropertyFilter
from apps.core.api.permissions import IsOwner, IsVerifiedOwner, IsSuperAdmin, AdminOrReadOnly, IsPropertyOwner

class PropertyViewSet(viewsets.ModelViewSet):
    """
    API REST de consultation et gestion des logements.
    - Publication publique (liste & détail des logements publiés)
    - Gestion par le propriétaire (création, modification, soumission)
    - Actions d'administration SuperAdmin (approbation, rejet, suspension)
    """
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'description', 'city', 'district']
    ordering_fields = ['price', 'created_at', 'surface']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'featured', 'nearby']:
            return [permissions.AllowAny()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'submit']:
            return [permissions.IsAuthenticated(), IsVerifiedOwner()]
        elif self.action in ['approve', 'reject', 'suspend', 'pending']:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            if getattr(user, 'is_superadmin', False) or user.is_superuser:
                return PropertySelector.get_all_properties()
            if getattr(user, 'is_owner', False):
                return PropertySelector.get_properties_for_owner(user.id)
        return PropertySelector.get_published_properties()

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyCreateUpdateSerializer
        return PropertyDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = PropertyCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        prop = PropertyService.create_property(
            owner=request.user,
            property_type_id=data.pop('property_type_id'),
            title=data.pop('title'),
            description=data.pop('description'),
            price=float(data.pop('price')),
            **data
        )
        return Response(PropertyDetailSerializer(prop).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        prop = self.get_object()
        serializer = PropertyCreateUpdateSerializer(data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        
        updated_prop = PropertyService.update_property(prop, owner=request.user, **serializer.validated_data)
        return Response(PropertyDetailSerializer(updated_prop).data)

    def destroy(self, request, *args, **kwargs):
        prop = self.get_object()
        PropertyService.delete_property(prop, owner=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        properties = PropertySelector.get_featured_properties(limit=6)
        serializer = PropertyListSerializer(properties, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        prop = self.get_object()
        prop = PropertyService.submit_for_validation(prop, owner=request.user)
        return Response({'detail': "Propriété soumise pour validation.", 'property': PropertyDetailSerializer(prop).data})

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        prop = self.get_object()
        prop = PropertyService.approve_property(prop, admin_user=request.user)
        prop = PropertyService.publish_property(prop, owner=prop.owner)
        return Response({'detail': "Propriété approuvée et publiée.", 'property': PropertyDetailSerializer(prop).data})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        prop = self.get_object()
        reason = request.data.get('reason', 'Refusé par l\'administrateur')
        prop = PropertyService.reject_property(prop, admin_user=request.user, reason=reason)
        return Response({'detail': "Propriété rejetée.", 'property': PropertyDetailSerializer(prop).data})


class PropertyCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyCategory.objects.filter(is_deleted=False)
    serializer_class = PropertyCategorySerializer
    permission_classes = [permissions.AllowAny]


class PropertyTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropertyType.objects.filter(is_deleted=False).select_related('category')
    serializer_class = PropertyTypeSerializer
    permission_classes = [permissions.AllowAny]


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PropertyFavorite.objects.filter(user=self.request.user, is_deleted=False).select_related('property')

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        property_id = request.data.get('property_id')
        if not property_id:
            return Response({'property_id': ["Ce champ est obligatoire."]}, status=status.HTTP_400_BAD_REQUEST)

        existing = PropertyFavorite.objects.filter(user=request.user, property_id=property_id).first()
        if existing:
            existing.delete()
            return Response({'detail': "Retiré des favoris.", 'is_favorite': False}, status=status.HTTP_200_OK)
        else:
            PropertyFavorite.objects.create(user=request.user, property_id=property_id)
            return Response({'detail': "Ajouté aux favoris.", 'is_favorite': True}, status=status.HTTP_201_CREATED)
