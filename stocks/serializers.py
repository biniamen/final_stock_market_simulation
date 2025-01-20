# stocks/serializers.py
#from datetime import timezone
from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone

from stocks.models_audit import TransactionAuditTrail
from django.contrib.auth import get_user_model

# Import everything ACTUALLY in `models.py`
from .models import (
    Disclosure, DividendDistribution, UsersPortfolio, ListedCompany,
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
            'company',           # MAKE SURE THIS IS INCLUDED
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


# class DividendSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Dividend
#         fields = '__all__'


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
  
  
      
# for dividend section 
class DividendDistributionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # To display username
    dividend = serializers.StringRelatedField(read_only=True)  # To display dividend info

    class Meta:
        model = DividendDistribution
        fields = ['id', 'dividend', 'user', 'amount', 'created_at']
        
class TradeWithOrderInfoSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.ticker_symbol', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)  # Optional
    company_name = serializers.CharField(source='stock.company.name', read_only=True)  # Optional
    order_type = serializers.CharField(source='order.order_type', read_only=True)  # From Order
    action = serializers.CharField(source='order.action', read_only=True)          # From Order
    order_id = serializers.CharField(source='order.id', read_only=True)          # From Order

    class Meta:
        model = Trade
        fields = [
            'id',
            'user_id',
            'username',           # Optional
            'quantity',
            'price',
            'transaction_fee',
            'trade_time',
            'order_type',         # Included from Order
            'action',             # Included from Order
            'stock_symbol',
            'company_name',       # Optional
            'order_id',
        ]
    
class TradeWithOrderInfoOutputSerializer(serializers.Serializer):
    """
    A simple serializer for the final 'Buy' trades with net holdings
    after FIFO subtraction. This is not tied to the Trade model directly,
    because we are building a custom output.
    """

    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    stock_symbol = serializers.CharField()
    order_type = serializers.CharField()
    price = serializers.CharField()
    quantity = serializers.IntegerField()
    transaction_fee = serializers.CharField()
    total_buying_price = serializers.CharField()
    weighted_value = serializers.CharField()
    dividend_eligible = serializers.CharField()
    trade_time = serializers.DateTimeField()
    
class HoldingSerializer(serializers.Serializer):
    stock_id = serializers.IntegerField()
    stock_symbol = serializers.CharField()
    quantity = serializers.IntegerField()

class UserBalanceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    net_balance = serializers.DecimalField(max_digits=20, decimal_places=2)
    holdings = HoldingSerializer(many=True)
    
class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = ['id', 'company', 'budget_year', 'dividend_ratio', 'total_dividend_amount', 'status']
        read_only_fields = ['id', 'dividend_ratio', 'status']

    def validate(self, attrs):
        """
        Ensure that no Dividend exists for the same company and budget_year.
        """
        company = attrs.get('company')
        budget_year = attrs.get('budget_year')

        if Dividend.objects.filter(company=company, budget_year=budget_year).exists():
            raise serializers.ValidationError(
                f"A dividend for company '{company}' in the year {budget_year} already exists."
            )

        return attrs

    def create(self, validated_data):
        # Automatically set 'budget_year' to the current year if not provided
        if 'budget_year' not in validated_data:
            validated_data['budget_year'] = timezone.now().year

        # Calculate 'dividend_ratio'
        total_dividend_amount = validated_data.get('total_dividend_amount')
        company = validated_data.get('company')

        # TODO: Replace with actual logic to fetch 'total_weighted_value'
        total_weighted_value = Decimal('1000.00')  # Example value; replace with real calculation

        if total_weighted_value == 0:
            raise serializers.ValidationError("Total weighted value cannot be zero.")

        validated_data['dividend_ratio'] = (total_dividend_amount / total_weighted_value).quantize(Decimal('0.0001'))

        return super().create(validated_data)