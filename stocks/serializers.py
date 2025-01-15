# stocks/serializers.py
from rest_framework import serializers

from stocks.models_audit import TransactionAuditTrail
from django.contrib.auth import get_user_model

# Import everything ACTUALLY in `models.py`
from .models import (
    Disclosure, UsersPortfolio, ListedCompany,
    Stocks, Orders, Trade, Dividend
)

# Import SuspiciousActivity from its own file
from .models_suspicious import SuspiciousActivity

User = get_user_model()

class UsersPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersPortfolio
        fields = ['id', 'user', 'quantity', 'average_purchase_price', 'total_investment']


class ListedCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListedCompany
        fields = '__all__'


# class StocksSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Stocks
#         fields = '__all__'

class StocksSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)

    class Meta:
        model = Stocks
        fields = [
            'id',
            'ticker_symbol',
            'total_shares',
            'current_price',
            'available_shares',
            'max_trader_buy_limit',
            'created_at',
            'company_name',
        ]
class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = ['user', 'stock', 'stock_symbol', 'order_type', 'action', 'price', 'quantity']

    def create(self, validated_data):
        return Orders.objects.create(**validated_data)


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = '__all__'


class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = '__all__'


class DirectStockPurchaseSerializer(serializers.Serializer):
    stock_symbol = serializers.CharField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

    def validate(self, attrs):
        stock_symbol = attrs.get('stock_symbol')
        quantity = attrs.get('quantity')
        try:
            stock = Stocks.objects.get(ticker_symbol=stock_symbol)
        except Stocks.DoesNotExist:
            raise serializers.ValidationError("Stock with the given symbol does not exist.")
        attrs['stock'] = stock
        return attrs


class DisclosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disclosure
        fields = ['id', 'company', 'type', 'year', 'file', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class SuspiciousActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SuspiciousActivity
        fields = '__all__'

class TradeWithOrderSerializer(serializers.ModelSerializer):
    # Pull fields from the Order table via the 'order' ForeignKey on Trade
    order_type = serializers.ReadOnlyField(source='order.order_type')
    action = serializers.ReadOnlyField(source='order.action')
    stock_symbol = serializers.ReadOnlyField(source='order.stock_symbol')
    
    class Meta:
        model = Trade
        # Include whichever Trade fields you need + the "extra" ones above
        fields = [
            'id',
            'quantity',
            'price',
            'transaction_fee',
            'trade_time',
            # Fields from the related Order (via read-only above)
            'order_type',
            'action',
            'stock_symbol',
        ]
# for Audit trail 
class TransactionAuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionAuditTrail
        fields = [
            'id',
            'event_type',
            'details',
            'timestamp',
            'order',
            'trade'
        ]
        
class UserBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']  # or whichever fields you want

class StockBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stocks
        fields = ['id', 'ticker_symbol']  # or whichever fields you want

class TradeDetailSerializer(serializers.ModelSerializer):
    user = UserBasicInfoSerializer(read_only=True)
    stock = StockBasicInfoSerializer(read_only=True)

    class Meta:
        model = Trade
        fields = [
            'id',
            'quantity',
            'price',
            'trade_time',
            'user',    # => { id, username, role, ... }
            'stock',   # => { id, ticker_symbol }
        ]

class SuspiciousActivityDetailSerializer(serializers.ModelSerializer):
    """
    SuspiciousActivity serializer that nests Trade data,
    which in turn nests User and Stock info.
    """
    trade = TradeDetailSerializer(read_only=True)

    class Meta:
        model = SuspiciousActivity
        fields = ['id', 'reason', 'flagged_at', 'reviewed', 'trade']