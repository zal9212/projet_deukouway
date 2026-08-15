from rest_framework import serializers
from apps.payments.models import Payment, Commission, Payout, Invoice

class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'reservation', 'user_email', 'amount', 'currency',
            'method', 'status', 'gateway_transaction_id', 'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'status', 'gateway_transaction_id', 'created_at']


class ProcessPaymentSerializer(serializers.Serializer):
    request_id = serializers.UUIDField(required=True)
    method = serializers.ChoiceField(choices=['WAVE', 'ORANGE_MONEY', 'CREDIT_CARD'], required=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    cardholder_name = serializers.CharField(required=False, allow_blank=True)
    card_number = serializers.CharField(required=False, allow_blank=True)
    card_expiry = serializers.CharField(required=False, allow_blank=True)
    card_cvc = serializers.CharField(required=False, allow_blank=True)


class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = ['id', 'payment', 'percentage_applied', 'amount', 'service_fee', 'created_at']


class PayoutSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Payout
        fields = [
            'id', 'owner_email', 'reservation', 'amount', 'currency',
            'method', 'status', 'gateway_transaction_id', 'created_at'
        ]
        read_only_fields = ['id', 'owner_email', 'status', 'gateway_transaction_id', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'reservation', 'file', 'created_at']
        read_only_fields = ['id', 'invoice_number', 'file', 'created_at']
