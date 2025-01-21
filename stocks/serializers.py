# stocks/serializers.py
#from datetime import timezone
from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from stocks.models_audit import TransactionAuditTrail
from django.contrib.auth import get_user_model

# Import everything ACTUALLY in `models.py`
from .models import (
    Disclosure, DividendDetailedHolding, DividendDistribution, UsersPortfolio, ListedCompany,
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
        fields = [
            'id', 'company', 'budget_year',
            'dividend_ratio', 'total_dividend_amount',
            'status'
        ]
        read_only_fields = ['id', 'dividend_ratio', 'status']

    def validate(self, attrs):
        """
        Ensure that no Dividend exists for the same company and budget_year.
        This is also enforced at the model level, but let's give a nice error message.
        """
        company = attrs.get('company')
        budget_year = attrs.get('budget_year')

        # If not set, default to current year
        if not budget_year:
            budget_year = str(timezone.now().year)
            attrs['budget_year'] = budget_year

        # Check existence
        if Dividend.objects.filter(company=company, budget_year=budget_year).exists():
            raise serializers.ValidationError(
                "A Dividend for this company and budget year already exists."
            )

        return attrs

    def create(self, validated_data):
        """
        Steps:
          1) get sum_weighted_value & holdingsData from request.data
          2) compute ratio
          3) create Dividend (status stays 'Pending' until we finalize)
          4) create DividendDetailedHolding rows
          5) for each 'Yes' => add to user profit_balance
          6) set Dividend status='Disbursed'
        """
        request_data = self.context['request'].data
        sum_weighted_value = request_data.get('sum_weighted_value', 0)
        holdings_data = request_data.get('holdingsData', [])

        if not sum_weighted_value or float(sum_weighted_value) == 0:
            raise serializers.ValidationError("sum_weighted_value must be > 0.")

        sum_weighted_value = Decimal(str(sum_weighted_value))
        total_div_amt = validated_data['total_dividend_amount']

        # 1) Compute ratio
        ratio = (Decimal(str(total_div_amt)) / sum_weighted_value).quantize(Decimal('0.000001'))

        with transaction.atomic():
            # 2) Create the Dividend (will still be 'Pending' at this instant)
            validated_data['dividend_ratio'] = ratio
            dividend = super().create(validated_data)  # calls ModelSerializer.create()

            # 3) Build DividendDetailedHolding rows
            holding_rows = []
            for row in holdings_data:
                wv = Decimal(str(row.get('weighted_value', '0')))
                paid_dividend = (ratio * wv).quantize(Decimal('0.01'))

                # Build the record
                holding_rows.append(DividendDetailedHolding(
                    dividend=dividend,
                    user_id=row.get('user_id'),
                    username=row.get('username', ''),
                    stock_symbol=row.get('stock_symbol', ''),
                    order_type=row.get('order_type', ''),
                    price=Decimal(str(row.get('price', '0'))),
                    quantity=row.get('quantity', 0),
                    transaction_fee=Decimal(str(row.get('transaction_fee', '0'))),
                    total_buying_price=Decimal(str(row.get('total_buying_price', '0'))),
                    weighted_value=wv,
                    dividend_eligible=row.get('dividend_eligible', 'No'),
                    trade_time=row.get('trade_time'),
                    ratio_at_creation=ratio,
                    paid_dividend=paid_dividend  # <--- newly added field
                ))

            # 3a) Bulk create them
            DividendDetailedHolding.objects.bulk_create(holding_rows)

            # 4) If dividend_eligible == "Yes", add to user.profit_balance
            for row in holdings_data:
                if row.get('dividend_eligible') == 'Yes':
                    user_id = row.get('user_id')
                    wv = Decimal(str(row.get('weighted_value', '0')))
                    paid_div = (ratio * wv).quantize(Decimal('0.01'))
                    if paid_div > 0:
                        user = User.objects.get(id=user_id)
                        # user.profit_balance could be zero if not set; set default to 0
                        current_balance = getattr(user, 'profit_balance', Decimal('0.00'))
                        user.profit_balance = current_balance + paid_div
                        user.save()

            # 5) Set the Dividend's status = 'Disbursed'
            dividend.status = 'Disbursed'
            dividend.save()

        return dividend