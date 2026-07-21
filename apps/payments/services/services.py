from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from apps.accounts.models import User
from apps.reservations.models import Reservation
from apps.payments.models import Payment, Commission, Payout, Invoice, Refund, PaymentHistory
from apps.payments.choices import PaymentStatusChoices, PayoutStatusChoices
from apps.payments.services.exceptions import PaymentAlreadyCompleted, InvalidAmount, PayoutAlreadyProcessed
import logging
import uuid

logger = logging.getLogger(__name__)

class PaymentService:

    @staticmethod
    def calculate_commission(amount: Decimal, percentage: Decimal = Decimal('15.00')) -> Decimal:
        """Calcule la commission DEKOUWAY à partir d'un montant de paiement."""
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
    def create_commission(payment: Payment, percentage: Decimal = Decimal('15.00')) -> Commission:
        amount = PaymentService.calculate_commission(payment.amount, percentage)
        
        commission = Commission.objects.create(
            payment=payment,
            percentage_applied=percentage,
            amount=amount,
            service_fee=Decimal('0.00')
        )
        logger.info(f"Commission créée : {commission.id} pour le paiement {payment.id}")
        return commission

    @staticmethod
    @transaction.atomic
    def create_payout(reservation: Reservation, owner: User, method: str) -> Payout:
        # Reversement = Total - Commission
        payment = reservation.payments.filter(status=PaymentStatusChoices.SUCCESS).first()
        if not payment:
            raise Exception("Aucun paiement terminé trouvé pour cette réservation.")
            
        commission = payment.commission
        if not commission:
            raise Exception("La commission doit être calculée avant le reversement.")
            
        payout_amount = payment.amount - commission.amount
        
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
        if payment.status != PaymentStatusChoices.COMPLETED:
            raise Exception("Impossible de rembourser un paiement non terminé.")
            
        refund = Refund.objects.create(
            payment=payment,
            amount=amount,
            reason=reason,
            status=PaymentStatusChoices.COMPLETED,
            gateway_transaction_id=str(uuid.uuid4())
        )
        
        old_status = payment.status
        payment.status = PaymentStatusChoices.FAILED
        payment.save(update_fields=['status'])
        
        PaymentHistory.objects.create(
            payment=payment,
            old_status=old_status,
            new_status=PaymentStatusChoices.FAILED,
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
