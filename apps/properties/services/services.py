from django.db import transaction
from django.utils import timezone
from apps.accounts.models import User
from apps.properties.models import Property, PropertyStatusHistory
from apps.properties.choices import PropertyStatusChoices
from apps.properties.services.exceptions import PropertyAlreadyPublished, InvalidPropertyStatus, UnauthorizedPropertyAction
import logging

logger = logging.getLogger(__name__)

class PropertyService:

    @staticmethod
    @transaction.atomic
    def create_property(owner: User, property_type_id: str, title: str, description: str, price: float, **kwargs) -> Property:
        prop = Property.objects.create(
            owner=owner,
            property_type_id=property_type_id,
            title=title,
            description=description,
            price=price,
            status=PropertyStatusChoices.DRAFT,
            **kwargs
        )
        logger.info(f"Propriété créée par le propriétaire {owner.email} : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def update_property(prop: Property, owner: User, **kwargs) -> Property:
        if prop.owner_id != owner.id:
            raise UnauthorizedPropertyAction("Vous ne pouvez pas modifier une propriété que vous ne possédez pas.")
            
        for key, value in kwargs.items():
            setattr(prop, key, value)
        prop.save()
        logger.info(f"Propriété mise à jour : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def submit_for_validation(prop: Property, owner: User) -> Property:
        if prop.owner_id != owner.id:
            raise UnauthorizedPropertyAction("Non autorisé.")
        
        if prop.status != PropertyStatusChoices.DRAFT:
            raise InvalidPropertyStatus("Seules les propriétés en brouillon peuvent être soumises.")

        old_status = prop.status
        prop.status = PropertyStatusChoices.PENDING
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.PENDING,
            reason="Soumis pour validation par le propriétaire"
        )
        
        logger.info(f"Propriété soumise pour validation : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def approve_property(prop: Property, admin_user: User) -> Property:
        if prop.status != PropertyStatusChoices.PENDING:
            raise InvalidPropertyStatus("La propriété n'est pas en attente de validation.")

        old_status = prop.status
        prop.status = PropertyStatusChoices.APPROVED
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.APPROVED,
            reason=f"Approuvé par {admin_user.email}"
        )
        
        logger.info(f"Propriété approuvée : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def reject_property(prop: Property, admin_user: User, reason: str) -> Property:
        if prop.status != PropertyStatusChoices.PENDING:
            raise InvalidPropertyStatus("La propriété n'est pas en attente de validation.")

        old_status = prop.status
        prop.status = PropertyStatusChoices.REJECTED
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.REJECTED,
            reason=reason
        )
        
        logger.warning(f"Propriété rejetée : {prop.id} - {reason}")
        return prop

    @staticmethod
    @transaction.atomic
    def publish_property(prop: Property, owner: User) -> Property:
        if prop.owner_id != owner.id:
            raise UnauthorizedPropertyAction("Non autorisé.")
            
        if prop.status == PropertyStatusChoices.PUBLISHED:
            raise PropertyAlreadyPublished("La propriété est déjà publiée.")
            
        if prop.status != PropertyStatusChoices.APPROVED:
            raise InvalidPropertyStatus("Seules les propriétés validées peuvent être publiées.")

        old_status = prop.status
        prop.status = PropertyStatusChoices.PUBLISHED
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.PUBLISHED,
            reason="Publié par le propriétaire"
        )
        
        logger.info(f"Propriété publiée : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def archive_property(prop: Property, owner: User) -> Property:
        if prop.owner_id != owner.id:
            raise UnauthorizedPropertyAction("Non autorisé.")

        old_status = prop.status
        prop.status = PropertyStatusChoices.ARCHIVED
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.ARCHIVED,
            reason="Archivé par le propriétaire"
        )
        
        logger.info(f"Propriété archivée : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def suspend_property(prop: Property, admin_user: User, reason: str) -> Property:
        old_status = prop.status
        prop.status = PropertyStatusChoices.SUSPENDED
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.SUSPENDED,
            reason=f"Suspendu par {admin_user.email} : {reason}"
        )
        
        logger.warning(f"Propriété suspendue : {prop.id} - {reason}")
        return prop

    @staticmethod
    @transaction.atomic
    def restore_property(prop: Property, admin_user: User) -> Property:
        if prop.status != PropertyStatusChoices.SUSPENDED:
            raise InvalidPropertyStatus("La propriété n'est pas suspendue.")

        old_status = prop.status
        prop.status = PropertyStatusChoices.VALIDATED
        prop.save(update_fields=['status'])
        
        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.VALIDATED,
            reason=f"Restauré par {admin_user.email}"
        )
        
        logger.info(f"Propriété restaurée : {prop.id}")
        return prop

    @staticmethod
    @transaction.atomic
    def delete_property(prop: Property, owner: User) -> None:
        if prop.owner_id != owner.id:
            raise UnauthorizedPropertyAction("Non autorisé.")
            
        prop.soft_delete()
        logger.info(f"Propriété supprimée logiquement : {prop.id}")
