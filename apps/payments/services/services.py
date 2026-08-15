from django.db import transaction
from decimal import Decimal
from apps.core.forms import validate_allowed_file_extensions, validate_file_content_type, validate_max_file_size
from apps.accounts.models import User
from apps.reservations.models import Reservation
from apps.payments.models import Payment, Commission, Payout, Invoice, Refund, PaymentHistory, PlatformSettings
from apps.payments.choices import PaymentStatusChoices, PayoutStatusChoices
from apps.payments.services.exceptions import (
    PaymentAlreadyCompleted, InvalidAmount, PayoutAlreadyProcessed,
    CompletedPaymentNotFound, CommissionNotCalculated, InvalidPaymentState,
)
import logging
import uuid

logger = logging.getLogger(__name__)

class PaymentService:

    @staticmethod
    def calculate_commission(amount: Decimal, percentage: Decimal = None) -> Decimal:
        """Calcule la commission DEKOUWAY à partir d'un montant de paiement."""
        if percentage is None:
            percentage = PlatformSettings.load().commission_percentage
        return (amount * percentage / Decimal('100')).quantize(Decimal('0.01'))

    @staticmethod
    @transaction.atomic
    def create_payment(reservation: Reservation, user: User, amount: Decimal, method: str) -> Payment:
        if amount <= 0:
            raise InvalidAmount("Le montant du paiement doit être supérieur à zéro.")
            
        payment = Payment.objects.create(
            reservation=reservation,
            user=user,
            amount=amount,
            method=method,
            status=PaymentStatusChoices.PENDING
        )
        
        PaymentHistory.objects.create(
            payment=payment,
            old_status=PaymentStatusChoices.PENDING,
            new_status=PaymentStatusChoices.PENDING,
            details={"action": "Paiement initialisé"}
        )
        
        logger.info(f"Paiement initialisé : {payment.id} pour {amount}")
        return payment

    @staticmethod
    @transaction.atomic
    def verify_payment(payment: Payment, gateway_transaction_id: str) -> Payment:
        if payment.status == PaymentStatusChoices.SUCCESS:
            raise PaymentAlreadyCompleted("Ce paiement est déjà terminé.")
            
        old_status = payment.status
        payment.status = PaymentStatusChoices.SUCCESS
        payment.gateway_transaction_id = gateway_transaction_id
        payment.save(update_fields=['status', 'gateway_transaction_id'])
        
        PaymentHistory.objects.create(
            payment=payment,
            old_status=old_status,
            new_status=PaymentStatusChoices.SUCCESS,
            details={"gateway_id": gateway_transaction_id}
        )
        
        logger.info(f"Paiement vérifié/terminé : {payment.id}")
        return payment

    @staticmethod
    @transaction.atomic
    def create_commission(payment: Payment, percentage: Decimal = None) -> Commission:
        if percentage is None:
            percentage = PlatformSettings.load().commission_percentage
        # Le tarif de la réservation (hors frais de service client) sert de base à la commission.
        base_amount = payment.reservation.total_price
        amount = PaymentService.calculate_commission(base_amount, percentage)
        service_fee = payment.amount - base_amount

        commission = Commission.objects.create(
            payment=payment,
            percentage_applied=percentage,
            amount=amount,
            service_fee=service_fee
        )
        logger.info(f"Commission créée : {commission.id} pour le paiement {payment.id}")
        return commission

    @staticmethod
    @transaction.atomic
    def create_payout(reservation: Reservation, owner: User, method: str) -> Payout:
        # Reversement = Total - Commission
        payment = reservation.payments.filter(status=PaymentStatusChoices.SUCCESS).first()
        if not payment:
            raise CompletedPaymentNotFound("Aucun paiement terminé trouvé pour cette réservation.")

        commission = payment.commission
        if not commission:
            raise CommissionNotCalculated("La commission doit être calculée avant le reversement.")
            
        payout_amount = payment.amount - commission.amount - commission.service_fee
        
        payout = Payout.objects.create(
            owner=owner,
            reservation=reservation,
            amount=payout_amount,
            method=method,
            status=PayoutStatusChoices.PENDING
        )
        logger.info(f"Reversement créé : {payout.id} pour le propriétaire {owner.email}")
        return payout

    @staticmethod
    @transaction.atomic
    def send_money_to_owner(payout: Payout, gateway_transaction_id: str) -> Payout:
        if payout.status == PayoutStatusChoices.COMPLETED:
            raise PayoutAlreadyProcessed("Le reversement est déjà terminé.")
            
        payout.status = PayoutStatusChoices.COMPLETED
        payout.gateway_transaction_id = gateway_transaction_id
        payout.save(update_fields=['status', 'gateway_transaction_id'])
        
        logger.info(f"Reversement terminé : {payout.id}")
        return payout

    @staticmethod
    @transaction.atomic
    def refund_payment(payment: Payment, amount: Decimal, reason: str) -> Refund:
        if payment.status != PaymentStatusChoices.SUCCESS:
            raise InvalidPaymentState("Impossible de rembourser un paiement non terminé.")

        refund = Refund.objects.create(
            payment=payment,
            amount=amount,
            reason=reason,
            status=PaymentStatusChoices.SUCCESS,
            gateway_transaction_id=str(uuid.uuid4())
        )

        old_status = payment.status
        payment.status = PaymentStatusChoices.REFUNDED
        payment.save(update_fields=['status'])

        PaymentHistory.objects.create(
            payment=payment,
            old_status=old_status,
            new_status=PaymentStatusChoices.REFUNDED,
            details={"action": "Remboursé", "refund_id": str(refund.id)}
        )
        
        logger.info(f"Paiement remboursé : {payment.id} pour {amount}")
        return refund

    @staticmethod
    @transaction.atomic
    def create_invoice(reservation: Reservation, user: User, file) -> Invoice:
        invoice = Invoice.objects.create(
            user=user,
            reservation=reservation,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            file=file
        )
        logger.info(f"Facture créée : {invoice.invoice_number}")
        return invoice

    @staticmethod
    def generate_receipt(payment: Payment) -> dict:
        """Logique de génération d'un reçu structuré."""
        return {
            "receipt_no": payment.id,
            "amount": payment.amount,
            "date": payment.created_at
        }

    @staticmethod
    @transaction.atomic
    def update_platform_settings(commission_percentage: Decimal, client_service_fee: Decimal) -> PlatformSettings:
        settings_obj = PlatformSettings.load()
        settings_obj.commission_percentage = commission_percentage
        settings_obj.client_service_fee = client_service_fee
        settings_obj.full_clean()
        settings_obj.save(update_fields=['commission_percentage', 'client_service_fee'])
        logger.info(f"Configuration plateforme mise à jour : commission={commission_percentage}%, frais={client_service_fee}")
        return settings_obj

    @staticmethod
    @transaction.atomic
    def update_branding_settings(site_name: str, logo=None, hero_image=None) -> PlatformSettings:
        settings_obj = PlatformSettings.load()
        update_fields = []

        if site_name:
            settings_obj.site_name = site_name
            update_fields.append('site_name')

        if logo is not None:
            validate_allowed_file_extensions(logo, ('png', 'jpg', 'jpeg'))
            validate_file_content_type(logo, ('png', 'jpg', 'jpeg'))
            validate_max_file_size(logo, max_size_mb=2.0)
            settings_obj.logo = logo
            update_fields.append('logo')

        if hero_image is not None:
            validate_allowed_file_extensions(hero_image, ('png', 'jpg', 'jpeg'))
            validate_file_content_type(hero_image, ('png', 'jpg', 'jpeg'))
            validate_max_file_size(hero_image, max_size_mb=5.0)
            settings_obj.hero_image = hero_image
            update_fields.append('hero_image')

        if update_fields:
            settings_obj.full_clean()
            settings_obj.save(update_fields=update_fields)
            logger.info(f"Identité de marque mise à jour : champs={update_fields}")
        return settings_obj
