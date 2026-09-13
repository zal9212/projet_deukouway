from decimal import Decimal
from django.db import transaction
from django.urls import reverse
from django.http import Http404
from apps.accounts.models import User
from apps.notifications.services.services import NotificationService
from apps.properties.models import Property, PropertyStatusHistory, PropertyAmenity, PropertyRule, PropertyImage, PropertyAvailability, PropertyReview
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
    def add_images(prop: Property, image_files: list, cover_index: int = 0) -> list:
        for image_file in image_files:
            validate_allowed_file_extensions(image_file, ('jpg', 'jpeg', 'png', 'webp'))
            validate_max_file_size(image_file, max_size_mb=15.0)
        created = []
        for index, image_file in enumerate(image_files):
            created.append(PropertyImage.objects.create(
                property=prop, image=image_file, is_cover=(index == cover_index), order=index
            ))
        return created

    @staticmethod
    @transaction.atomic
    def delete_image(image_id, owner: User, prop: Property = None) -> None:
        """
        Supprime une photo d'une annonce.
        Empêche la suppression si l'annonce est publiée et qu'il s'agit de la dernière photo.
        """
        try:
            image = PropertyImage.objects.select_related('property').get(id=image_id)
        except PropertyImage.DoesNotExist:
            raise Http404("Photo non trouvée.")

        property_obj = prop or image.property
        is_owner = str(property_obj.owner_id) == str(owner.id)
        is_admin = getattr(owner, 'is_superadmin', False) or getattr(owner, 'is_staff', False) or getattr(owner, 'is_superuser', False)
        if not (is_owner or is_admin):
            raise UnauthorizedPropertyAction("Vous ne pouvez pas supprimer une photo de cette annonce.")

        # Règle de publication : une annonce publiée ne peut pas être vidée de toutes ses photos
        if property_obj.status in [PropertyStatusChoices.PUBLISHED, PropertyStatusChoices.ACTIVE]:
            remaining_count = property_obj.images.count()
            if remaining_count <= 1:
                raise InvalidPropertyStatus(
                    "Impossible de supprimer la seule photo d'une annonce publiée. "
                    "Veuillez ajouter une autre photo avant de supprimer celle-ci."
                )

        was_cover = image.is_cover
        image.delete()

        # Si l'image était la photo de couverture, promouvoir la première restante
        if was_cover:
            next_img = property_obj.images.first()
            if next_img:
                next_img.is_cover = True
                next_img.save(update_fields=['is_cover'])

        logger.info(f"Photo {image_id} supprimée de l'annonce {property_obj.id} par {owner.email}")

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
        NotificationService.notify_owner(
            prop.owner, "Annonce validée",
            f"Votre annonce « {prop.title} » a été validée par notre équipe.",
            link=reverse('dashboard:owner_edit_property', kwargs={'pk': prop.pk})
        )
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
        NotificationService.notify_owner(
            prop.owner, "Annonce rejetée",
            f"Votre annonce « {prop.title} » a été rejetée. Motif : {reason}",
            link=reverse('dashboard:owner_edit_property', kwargs={'pk': prop.pk})
        )
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

    @staticmethod
    @transaction.atomic
    def create_review(user: User, property_id: str, rating: int, comment: str = "", reservation_id: str = None) -> PropertyReview:
        """
        Dépose un avis et une note sur une propriété après un séjour terminé.
        Vérifie l'existence d'une réservation terminée et empêche les doublons.
        """
        from apps.reservations.models import Reservation
        from apps.reservations.choices import ReservationStatusChoices
        from django.utils import timezone

        try:
            prop = Property.objects.get(id=property_id, is_deleted=False)
        except Property.DoesNotExist:
            raise Http404("Logement non trouvé.")

        if rating < 1 or rating > 5:
            raise InvalidPropertyStatus("La note doit être comprise entre 1 et 5.")

        res_query = Reservation.objects.filter(
            property=prop,
            client=user,
            is_deleted=False
        )
        if reservation_id:
            res_query = res_query.filter(id=reservation_id)

        # Une réservation est éligible si son statut est COMPLETED ou si elle est CONFIRMED avec date de fin échue
        eligible_reservation = None
        for res in res_query:
            if res.status == ReservationStatusChoices.COMPLETED or (
                res.status == ReservationStatusChoices.CONFIRMED and res.end_date <= timezone.now().date()
            ):
                eligible_reservation = res
                break

        if not eligible_reservation:
            raise UnauthorizedPropertyAction("Vous devez avoir effectué et terminé un séjour dans ce logement pour pouvoir y déposer un avis.")

        if PropertyReview.objects.filter(reservation=eligible_reservation).exists():
            raise InvalidPropertyStatus("Un avis a déjà été déposé pour ce séjour.")

        review = PropertyReview.objects.create(
            property=prop,
            user=user,
            reservation=eligible_reservation,
            rating=rating,
            comment=comment
        )

        try:
            NotificationService.notify_owner(
                owner=prop.owner,
                title="Nouvel avis reçu",
                message=f"{user.get_full_name() or user.email} a attribué la note de {rating}/5 à votre logement '{prop.title}'.",
                link=f"/espace/annonces/{prop.id}/"
            )
        except Exception as e:
            logger.warning("Échec de notification propriétaire lors du dépôt d'avis : %s", e)

        logger.info(f"Avis créé pour le logement {prop.id} par {user.email} (note: {rating}/5)")
        return review
