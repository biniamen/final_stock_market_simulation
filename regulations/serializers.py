from rest_framework import serializers
from .models import Regulation, AuditLog, StockSuspension, WorkingHours
from django.contrib.auth import get_user_model
from stocks.models import Stocks  # Ensure you have the Stocks model imported
User = get_user_model()


class RegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regulation
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class StockSuspensionSerializer(serializers.ModelSerializer):
    trader_username = serializers.CharField(source='trader.username', read_only=True)
    stock_ticker_symbol = serializers.CharField(source='stock.ticker_symbol', read_only=True)

    class Meta:
        model = StockSuspension
        fields = [
            'id',
            'suspension_type',
            'initiator',
            'reason',
            'is_active',
            'created_at',
            'released_at',
            'trader',
            'trader_username',          # New field
            'stock',
            'stock_ticker_symbol',      # New field
        ]

class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = '__all__'