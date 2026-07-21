from django.db.models import QuerySet
from apps.properties.models import Property
from apps.properties.choices import PropertyStatusChoices

class PropertySelector:
    
    @staticmethod
    def get_property_by_id(property_id: str) -> Property | None:
        return Property.objects.filter(id=property_id, is_deleted=False).first()
        
    @staticmethod
    def get_properties_for_owner(owner_id: str) -> QuerySet[Property]:
        return Property.objects.filter(owner_id=owner_id, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_published_properties() -> QuerySet[Property]:
        return Property.objects.filter(
            status=PropertyStatusChoices.PUBLISHED, 
            is_deleted=False
        ).select_related('property_type').prefetch_related('images')
