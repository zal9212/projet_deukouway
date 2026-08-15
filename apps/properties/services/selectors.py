from django.db.models import QuerySet, Q, Avg, Count
from django.core.cache import cache
from django.conf import settings
from apps.properties.models import Property, PropertyCategory, PropertyType, PropertyFavorite, PropertyAvailability
from apps.properties.choices import PropertyStatusChoices

class PropertySelector:

    @staticmethod
    def get_blocked_dates(property_id: str, start_date, end_date) -> set:
        """Retourne l'ensemble des dates bloquées (indisponibles) pour ce logement dans l'intervalle donné."""
        return set(
            PropertyAvailability.objects.filter(
                property_id=property_id, is_available=False, is_deleted=False,
                date__gte=start_date, date__lte=end_date,
            ).values_list('date', flat=True)
        )

    @staticmethod
    def get_property_by_id(property_id: str) -> Property | None:
        return Property.objects.filter(id=property_id, is_deleted=False).select_related('owner', 'property_type', 'property_type__category').prefetch_related('images', 'amenities', 'rules').first()

    @staticmethod
    def get_properties_for_owner(owner_id: str, search_query: str = None, status: str = None) -> QuerySet[Property]:
        qs = Property.objects.filter(owner_id=owner_id, is_deleted=False).select_related('property_type').prefetch_related('images')
        if search_query:
            qs = qs.filter(Q(title__icontains=search_query) | Q(city__icontains=search_query) | Q(district__icontains=search_query))
        if status == 'published':
            qs = qs.filter(status=PropertyStatusChoices.PUBLISHED)
        elif status == 'pending':
            qs = qs.filter(status__in=[PropertyStatusChoices.PENDING, PropertyStatusChoices.UNDER_REVIEW])
        elif status == 'draft':
            qs = qs.filter(status=PropertyStatusChoices.DRAFT)
        return qs.order_by('-created_at')

    @staticmethod
    def get_published_properties() -> QuerySet[Property]:
        return Property.objects.filter(
            status=PropertyStatusChoices.PUBLISHED,
            is_deleted=False
        ).select_related('owner', 'property_type').prefetch_related('images').annotate(
            avg_rating=Avg('reviews__rating'), review_count=Count('reviews', distinct=True)
        ).order_by('-created_at')

    @staticmethod
    def get_featured_properties(limit: int = 6) -> QuerySet[Property]:
        return PropertySelector.get_published_properties()[:limit]

    @staticmethod
    def get_similar_properties(prop: Property, limit: int = 4) -> QuerySet[Property]:
        qs = PropertySelector.get_published_properties().exclude(id=prop.id)
        same_city = qs.filter(city=prop.city)
        if same_city.count() >= limit:
            return same_city[:limit]
        # Complète avec des logements du même type si la ville n'a pas assez de résultats.
        extra_ids = list(same_city.values_list('id', flat=True))
        extra = qs.filter(property_type=prop.property_type).exclude(id__in=extra_ids)[:limit - len(extra_ids)]
        return list(same_city) + list(extra)

    @staticmethod
    def get_pending_properties() -> QuerySet[Property]:
        return Property.objects.filter(
            status=PropertyStatusChoices.PENDING,
            is_deleted=False
        ).select_related('owner', 'property_type').order_by('-created_at')

    @staticmethod
    def get_all_properties(search_query: str = None, status: str = None) -> QuerySet[Property]:
        qs = Property.objects.filter(is_deleted=False).select_related('owner', 'property_type')
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(owner__email__icontains=search_query)
            )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    @staticmethod
    def search_properties(
        query: str | None = None,
        city: str | None = None,
        district: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        property_type: str | None = None,
        sort_by: str | None = None,
        min_bedrooms: int | None = None,
        min_bathrooms: int | None = None,
        amenities: list | None = None,
    ) -> QuerySet[Property]:
        qs = PropertySelector.get_published_properties()
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(city__icontains=query) | Q(district__icontains=query))
        if city:
            qs = qs.filter(city__iexact=city)
        if district:
            qs = qs.filter(district__icontains=district)
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        if property_type:
            qs = qs.filter(property_type__slug=property_type)
        if min_bedrooms is not None:
            qs = qs.filter(bedrooms__gte=min_bedrooms)
        if min_bathrooms is not None:
            qs = qs.filter(bathrooms__gte=min_bathrooms)
        for amenity_name in (amenities or []):
            qs = qs.filter(amenities__name__icontains=amenity_name)
        if amenities:
            qs = qs.distinct()

        if sort_by == 'price_asc':
            qs = qs.order_by('price')
        elif sort_by == 'price_desc':
            qs = qs.order_by('-price')
        elif sort_by == 'newest':
            qs = qs.order_by('-created_at')
            
        return qs

    @staticmethod
    def get_user_favorites(user_id: str) -> QuerySet[Property]:
        favorite_ids = PropertyFavorite.objects.filter(user_id=user_id, is_deleted=False).values_list('property_id', flat=True)
        return Property.objects.filter(id__in=favorite_ids, is_deleted=False).select_related('property_type').prefetch_related('images').annotate(
            avg_rating=Avg('reviews__rating'), review_count=Count('reviews', distinct=True)
        ).order_by('-created_at')

    @staticmethod
    def get_user_favorite_ids(user_id: str) -> set:
        if not user_id:
            return set()
        return set(PropertyFavorite.objects.filter(user_id=user_id, is_deleted=False).values_list('property_id', flat=True))

    @staticmethod
    def get_all_categories() -> list:
        # Table de référence quasi-statique, relue sur presque chaque page publique
        # et chaque formulaire propriétaire : cache long, invalidé manuellement si
        # une catégorie est ajoutée/modifiée (rare, via l'admin Django).
        if settings.TESTING:
            return list(PropertyCategory.objects.filter(is_deleted=False))
        cached = cache.get('property_categories')
        if cached is not None:
            return cached
        categories = list(PropertyCategory.objects.filter(is_deleted=False))
        cache.set('property_categories', categories, timeout=3600)
        return categories

    @staticmethod
    def get_all_types() -> list:
        if settings.TESTING:
            return list(PropertyType.objects.filter(is_deleted=False).select_related('category'))
        cached = cache.get('property_types')
        if cached is not None:
            return cached
        types = list(PropertyType.objects.filter(is_deleted=False).select_related('category'))
        cache.set('property_types', types, timeout=3600)
        return types
