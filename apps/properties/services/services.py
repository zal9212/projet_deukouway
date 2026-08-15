from decimal import Decimal
from django.db import transaction
from apps.accounts.models import User
from apps.properties.models import Property, PropertyStatusHistory, PropertyAmenity, PropertyRule, PropertyImage, PropertyAvailability
from apps.properties.choices import PropertyStatusChoices, PropertyPricingPeriodChoices
from apps.properties.services.exceptions import PropertyAlreadyPublished, InvalidPropertyStatus, UnauthorizedPropertyAction, DatesAlreadyBooked
from apps.core.forms import validate_max_file_size, validate_allowed_file_extensions
import datetime
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
    def calculate_price_for_stay(prop: Property, check_in, check_out) -> Decimal:
        """
        Calcule le sous-total du séjour à partir du tarif du logement. Un logement
        "Par mois" affiche un prix mensuel : on le proratise sur 30 jours plutôt que
        de le multiplier tel quel par le nombre de nuits (ce qui produirait un montant
        absurde, ex: prix mensuel × 7 nuits).
        """
        nights = max((check_out - check_in).days, 1)
        price = Decimal(str(prop.price))
        if prop.pricing_period == PropertyPricingPeriodChoices.MONTHLY:
            return (price / Decimal('30') * Decimal(nights)).quantize(Decimal('0.01'))
        return price * Decimal(nights)

    @staticmethod
    @transaction.atomic
    def add_amenities(prop: Property, amenity_names: list) -> None:
        PropertyAmenity.objects.bulk_create([
            PropertyAmenity(property=prop, name=name) for name in amenity_names if name and name.strip()
        ])

    @staticmethod
    @transaction.atomic
    def add_rules(prop: Property, rule_texts: list) -> None:
        PropertyRule.objects.bulk_create([
            PropertyRule(property=prop, rule=rule) for rule in rule_texts if rule and rule.strip()
        ])

    @staticmethod
    @transaction.atomic
    def set_amenities(prop: Property, amenity_names: list) -> None:
        """Remplace la liste d'équipements du logement (utilisé lors d'une modification)."""
        prop.amenities.all().delete()
        PropertyService.add_amenities(prop, amenity_names)

    @staticmethod
    @transaction.atomic
    def set_rules(prop: Property, rule_texts: list) -> None:
        """Remplace la liste de règles du logement (utilisé lors d'une modification)."""
        prop.rules.all().delete()
        PropertyService.add_rules(prop, rule_texts)

    @staticmethod
    @transaction.atomic
    def add_images(prop: Property, image_files: list, cover_index: int = 0) -> None:
        for image_file in image_files:
            validate_allowed_file_extensions(image_file, ('jpg', 'jpeg', 'png', 'webp'))
            validate_max_file_size(image_file, max_size_mb=8.0)
        for index, image_file in enumerate(image_files):
            PropertyImage.objects.create(
                property=prop, image=image_file, is_cover=(index == cover_index), order=index
            )

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
        prop.status = PropertyStatusChoices.PUBLISHED
        prop.save(update_fields=['status'])

        PropertyStatusHistory.objects.create(
            property=prop,
            old_status=old_status,
            new_status=PropertyStatusChoices.PUBLISHED,
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

    @staticmethod
    @transaction.atomic
    def block_dates(prop: Property, owner: User, start_date, end_date, reason: str = "") -> int:
        """Bloque une plage de dates (maintenance/usage personnel) sur le calendrier du logement."""
        from apps.reservations.services.selectors import ReservationSelector

        if prop.owner_id != owner.id:
            raise UnauthorizedPropertyAction("Non autorisé.")
        if end_date < start_date:
            raise InvalidPropertyStatus("La date de fin doit être postérieure à la date de début.")
        if ReservationSelector.has_overlapping_active_booking(prop.id, start_date, end_date + datetime.timedelta(days=1)):
            raise DatesAlreadyBooked("Ces dates chevauchent une réservation ou une demande active. Impossible de les bloquer.")

        current = start_date
        count = 0
        while current <= end_date:
            _, created = PropertyAvailability.objects.update_or_create(
                property=prop, date=current, defaults={'is_available': False}
            )
            count += 1
            current += datetime.timedelta(days=1)

        logger.info(f"{count} date(s) bloquée(s) pour la propriété {prop.id} par {owner.email} : {reason}")
        return count
