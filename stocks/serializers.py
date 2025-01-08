from rest_framework import serializers
from .models import Disclosure, SuspiciousActivity, UsersPortfolio, ListedCompany, Stocks, Orders, Trade, Dividend


class UsersPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersPortfolio
        fields = '__all__'


class ListedCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListedCompany
        fields = '__all__'


class StocksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stocks
        fields = '__all__'


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = ['user', 'stock', 'stock_symbol', 'order_type', 'action', 'price', 'quantity']

    def create(self, validated_data):
        # The Orders model logic or signals handle the matching and saving
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

        # Check if stock exists
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