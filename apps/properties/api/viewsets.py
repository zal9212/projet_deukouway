from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.properties.services.selectors import PropertySelector
from apps.properties.services.services import PropertyService
from apps.properties.models import PropertyCategory, PropertyType, PropertyFavorite
from apps.properties.api.serializers import (
    PropertyListSerializer, PropertyDetailSerializer, PropertyCreateUpdateSerializer,
    PropertyCategorySerializer, PropertyTypeSerializer, PropertyFavoriteSerializer,
    PropertyReviewSerializer, PropertyReviewCreateSerializer
)
from apps.properties.api.filters import PropertyFilter
from apps.core.api.permissions import IsVerifiedOwner, IsSuperAdmin

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

    @action(detail=True, methods=['post'], url_path='images')
    def add_images(self, request, pk=None):
        prop = self.get_object()
        files = request.FILES.getlist('images') or ([request.FILES['image']] if 'image' in request.FILES else [])
        if not files:
            return Response({'images': ["Aucune photo fournie."]}, status=status.HTTP_400_BAD_REQUEST)

        from apps.properties.api.serializers import PropertyImageSerializer
        cover_index = 0 if not prop.images.exists() else -1
        image_objs = PropertyService.add_images(prop, files, cover_index=cover_index)
        return Response({
            'detail': f"{len(files)} photo(s) ajoutée(s).",
            'images': PropertyImageSerializer(image_objs, many=True).data,
        }, status=status.HTTP_201_CREATED)

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

    @action(detail=True, methods=['delete'], url_path=r'images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        prop = self.get_object()
        PropertyService.delete_image(image_id=image_id, owner=request.user, prop=prop)
        return Response({'detail': "Photo supprimée avec succès."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'], url_path='reviews')
    def reviews(self, request, pk=None):
        prop = self.get_object()
        if request.method == 'GET':
            reviews = prop.reviews.filter(is_deleted=False).select_related('user')
            return Response(PropertyReviewSerializer(reviews, many=True).data)

        if not request.user or not request.user.is_authenticated:
            return Response({'detail': "Authentification requise pour déposer un avis."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = PropertyReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        review = PropertyService.create_review(
            user=request.user,
            property_id=str(prop.id),
            rating=data['rating'],
            comment=data.get('comment', ''),
            reservation_id=str(data['reservation_id']) if data.get('reservation_id') else None
        )
        return Response(PropertyReviewSerializer(review).data, status=status.HTTP_201_CREATED)


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
