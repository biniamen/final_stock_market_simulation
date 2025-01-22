from collections import defaultdict
import datetime
from decimal import Decimal
from django.forms import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
import datetime
from django.utils import timezone
from django.db.models import Sum, F, Q, DecimalField, ExpressionWrapper
from django.utils.timezone import make_aware,now

from stocks import permissions
from rest_framework import generics
from stocks.dividend_calculation import distribute_dividend
from stocks.models_audit import TransactionAuditTrail
from stocks.permissions import IsRegulator, IsRegulatorUser, IsTrader
from .models import Disclosure, DividendDetailedHolding, DividendDistribution, UsersPortfolio, ListedCompany, Stocks, Orders, Trade, Dividend
from .serializers import (
    DirectStockPurchaseSerializer,
    DisclosureSerializer,
    DividendDetailedHoldingSerializer,
    DividendDistributionSerializer,
    RegulatorDividendSerializer,
    SuspiciousActivityDetailSerializer,
    TradeWithOrderInfoOutputSerializer,
    TradeWithOrderInfoSerializer,
    TradeWithOrderSerializer,
    TraderDividendSerializer,
    TransactionAuditTrailSerializer,
    UserBalanceSerializer,
    UsersPortfolioSerializer,
    ListedCompanySerializer,
    StocksSerializer,
    OrdersSerializer,
    TradeSerializer,
    DividendSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models_suspicious import SuspiciousActivity
from .serializers import SuspiciousActivitySerializer
from django.db import transaction
from django.contrib.auth import get_user_model

import logging

from stocks import serializers
logger = logging.getLogger(__name__)
User = get_user_model()


# class UsersPortfolioViewSet(viewsets.ModelViewSet):
#     queryset = UsersPortfolio.objects.all()
#     serializer_class = UsersPortfolioSerializer


class ListedCompanyViewSet(viewsets.ModelViewSet):
    queryset = ListedCompany.objects.all()
    serializer_class = ListedCompanySerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new listed company and return the serialized data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# class StocksViewSet(viewsets.ModelViewSet):
#     queryset = Stocks.objects.all()
#     serializer_class = StocksSerializer

class StocksViewSet(viewsets.ModelViewSet):
    queryset = Stocks.objects.select_related('company').all()
    serializer_class = StocksSerializer

class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new order and automatically execute matching orders.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()  # Automatically triggers matching logic
        return Response(
            {
                "message": "Order created and matching executed successfully.",
                "order": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

class TraderOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is a trader
        if request.user.role != 'trader':
            return Response({"detail": "Only traders can view this resource."}, status=403)
        
        # Fetch orders belonging to the logged-in trader
        orders = Orders.objects.filter(trader=request.user)
        serializer = OrdersSerializer(orders, many=True)
        return Response(serializer.data)

class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch orders belonging to the logged-in user
        orders = Orders.objects.filter(user=request.user)
        serializer = OrdersSerializer(orders, many=True)
        return Response(serializer.data)

class UserTradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch trades belonging to the logged-in user
        trades = Trade.objects.filter(user=request.user)
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)

# class DividendViewSet(viewsets.ModelViewSet):
#     queryset = Dividend.objects.all()
#     serializer_class = DividendSerializer
#     #permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]  # Adjust permissions as needed


class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        dividend = serializer.save()
        # serializer.save() will do all the ratio logic & set status to Disbursed
        return Response(self.get_serializer(dividend).data, status=status.HTTP_201_CREATED)
    
    
class DirectStockPurchaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user  # Get the authenticated user
        stock_id = request.data.get("stock_id")
        quantity = request.data.get("quantity")

        # Validate input fields
        if stock_id is None or quantity is None:
            return Response(
                {"detail": "Both 'stock_id' and 'quantity' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate quantity is a positive integer
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"detail": "Quantity must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid value for 'quantity'. It must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Execute direct purchase without creating duplicate Trade entries
                order, trade = Stocks.execute_direct_purchase(user.id, stock_id, quantity)
                updated_balance = user.account_balance
                updated_profit = getattr(user, 'profit_balance', None)  # Safely get profit_balance

            response_data = {
                "message": "Direct purchase completed successfully.",
                "order_id": order.id,
                "trade_id": trade.id,
                "stock_symbol": order.stock_symbol,
                "quantity": order.quantity,
                "price": str(order.price),
                "total_cost": str(order.price * order.quantity),
                "transaction_fee": str(order.transaction_fee),
                "total_deducted": str(order.price * order.quantity + order.transaction_fee),
                "status": order.status,
                "updated_balance": str(updated_balance),
            }

            if updated_profit is not None:
                response_data["profit_balance"] = str(updated_profit)

            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # Return specific validation errors
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log the unexpected error for debugging
            logger.error(f"Unexpected error during direct stock purchase: {str(e)}")
            # For debugging purposes, return the error message
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserSpecificTradesView(APIView):
    """
    GET /api/stocks/user/<user_id>/trades/
    Returns all trades for the specified user.
    """
    def get(self, request, user_id, *args, **kwargs):
        # Fetch all trades for the given user_id
        trades = Trade.objects.filter(user_id=user_id)
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DisclosureViewSet(viewsets.ModelViewSet):
    queryset = Disclosure.objects.all()
    serializer_class = DisclosureSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Check user role
        if hasattr(request.user, 'role') and request.user.role != 'company_admin':
            return Response({"detail": "Only company admins can upload disclosures."},
                            status=status.HTTP_403_FORBIDDEN)

        # Validate for duplicate disclosure
        company = request.data.get('company')
        year = request.data.get('year')
        disclosure_type = request.data.get('type')

        if Disclosure.objects.filter(company=company, year=year, type=disclosure_type).exists():
            return Response(
                {"detail": "A disclosure with the same type and year already exists for this company."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save the disclosure
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        disclosure = serializer.save()
        return Response({
            "message": "Disclosure uploaded successfully.",
            "disclosure": self.get_serializer(disclosure).data
        }, status=status.HTTP_201_CREATED)

class CompanyDisclosuresView(APIView):
    """
    Fetch disclosures for a specific company.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id, *args, **kwargs):
        # Query disclosures for the specific company
        disclosures = Disclosure.objects.filter(company_id=company_id)
        serializer = DisclosureSerializer(disclosures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    
        
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])  # or staff-only permission
def suspicious_activities(request):
    """
    GET:  Retrieves unreviewed suspicious activities (staff only).
    POST: Marks a suspicious activity as reviewed by ID (staff only).
    """
    if not request.user.is_staff:
        return Response({"error": "Only staff can manage suspicious activities."}, status=403)

    if request.method == 'GET':
        activities = SuspiciousActivity.objects.filter(reviewed=False)
        serializer = SuspiciousActivitySerializer(activities, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        activity_id = request.data.get('activity_id')
        if not activity_id:
            return Response({"error": "activity_id is required."}, status=400)

        activity = get_object_or_404(SuspiciousActivity, id=activity_id)
        activity.reviewed = True
        activity.save()
        return Response({"message": "Activity marked as reviewed."})
    
class UsersPortfolioViewSet(viewsets.ModelViewSet):
    queryset = UsersPortfolio.objects.all()
    serializer_class = UsersPortfolioSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def get_portfolio_by_user(self, request, user_id=None):
        """
        Retrieve a user's portfolio by their user ID and include account_balance and profit_balance.
        """
        try:
            user_id = int(user_id)
        except ValueError:
            return Response(
                {'detail': 'Invalid user ID format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check permissions: users can only access their own portfolio unless they're admins
        if not request.user.is_staff and request.user.id != user_id:
            raise PermissionDenied("You do not have permission to view this portfolio.")

        try:
            portfolio = UsersPortfolio.objects.get(user__id=user_id)
            user = portfolio.user  # Fetch the associated user
            serializer = self.get_serializer(portfolio)
            portfolio_data = serializer.data
            # Include account_balance and profit_balance from the user model
            portfolio_data['account_balance'] = user.account_balance
            portfolio_data['profit_balance'] = user.profit_balance
            return Response(portfolio_data, status=status.HTTP_200_OK)
        except UsersPortfolio.DoesNotExist:
            return Response(
                {'detail': 'Portfolio not found for the given user ID.'},
                status=status.HTTP_404_NOT_FOUND
            )

            
class UserTradesWithOrderInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        """
        Returns trades for a given user_id, including order_type, action, and stock_symbol from the Order model.
        """
        trades = Trade.objects.filter(user_id=user_id)
        serializer = TradeWithOrderSerializer(trades, many=True)
        return Response(serializer.data, status=200)
    
# for audit trail
class TransactionAuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing transaction audit trails.
    """
    queryset = TransactionAuditTrail.objects.all().order_by('-timestamp')
    serializer_class = TransactionAuditTrailSerializer
    permission_classes = [IsAuthenticated]
    
    
#susupicious activity 
class SuspiciousActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing/creating/updating suspicious activities.
    Access restricted to 'regulator' role only.
    """
    queryset = SuspiciousActivity.objects.all().order_by('-flagged_at')
    serializer_class = SuspiciousActivityDetailSerializer
    permission_classes = [IsRegulatorUser]  # Only 'regulator' role can access

    @action(detail=True, methods=['post'], url_path='suspend-trader')
    def suspend_trader(self, request, pk=None):
        """
        POST /suspicious-activities/<id>/suspend-trader/
        Creates a StockSuspension record for the user involved in the suspicious activity's trade.
        Globally suspends them (All Stocks).
        """
        suspicious_activity = self.get_object()

        # Ensure there's a trade associated
        if not suspicious_activity.trade:
            return Response(
                {"detail": "This suspicious activity has no associated trade."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # We'll suspend the user associated with that trade
        trader_user = suspicious_activity.trade.user

        # Create the suspension (All Stocks by default)
        suspension = StockSuspension.objects.create(
            trader=trader_user,
            stock=None,  # means "All Stocks"
            suspension_type='All Stocks',
            initiator='Regulatory Body',
            reason=f"Suspicious Activity (ID: {suspicious_activity.id}). Reason: {suspicious_activity.reason}",
            is_active=True,
            created_at=now()
        )

        return Response(
            {
                "message": f"Trader {trader_user.username} has been suspended from all stocks.",
                "suspension_id": suspension.id
            },
            status=status.HTTP_200_OK
        )

class DistributeDividendView(APIView):
    """
    POST /api/stocks/dividends/<dividend_id>/distribute/
    """
    def post(self, request, dividend_id):
        # Optionally check that user is "company_admin" or "staff" or some permission
        # For now, we assume only certain roles can do this:
        # if not request.user.is_staff:
        #     return Response(
        #         {"detail": "Only staff or company admins can distribute dividends."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        try:
            with transaction.atomic():
                distributions = distribute_dividend(dividend_id, executed_by=request.user)
            return Response({
                "message": "Dividend distributed successfully.",
                "num_distributions": len(distributions)
            }, status=status.HTTP_200_OK)
        except Dividend.DoesNotExist:
            return Response(
                {"detail": "Dividend not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error distributing dividend {dividend_id}: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class DividendDistributionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Dividend Distributions.
    """
    queryset = DividendDistribution.objects.all().order_by('-created_at')
    serializer_class = DividendDistributionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally restricts the returned distributions to a given dividend or user,
        by filtering against query parameters in the URL.
        """
        queryset = self.queryset
        dividend_id = self.request.query_params.get('dividend_id')
        user_id = self.request.query_params.get('user_id')
        if dividend_id:
            queryset = queryset.filter(dividend__id=dividend_id)
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        return queryset
    
    
class StockTradesWithOrderInfoView(APIView):
    """
    API View to retrieve all trades for a given stock_id with user and order info.
    """
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request, stock_id, format=None):
        try:
            # Validate that the stock exists
            stock = Stocks.objects.get(id=stock_id)
        except Stocks.DoesNotExist:
            return Response(
                {"error": "Stock not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Fetch all trades related to the stock
        trades = Trade.objects.filter(stock=stock).select_related('user', 'stock').order_by('-trade_time')

        # Serialize the data
        serializer = TradeWithOrderInfoSerializer(trades, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class StockNetHoldingsView(APIView):
    """
    API View to retrieve net BUY holdings for a given stock_id, after FIFO
    subtraction of SELL trades. Returns only the leftover 'Buy' trades with
    correct quantities, plus weighted_value and dividend_eligible calculations.
    """
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request, stock_id):
        # 1. Validate the Stock
        try:
            stock = Stocks.objects.get(id=stock_id)
        except Stocks.DoesNotExist:
            return Response({"error": "Stock not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Query all trades for this stock, sorted by trade_time ascending
        trades = Trade.objects.filter(stock=stock).select_related('user', 'stock', 'order').order_by('trade_time')

        # 3. Determine current_price (from query param or database)
        current_price_param = request.query_params.get('current_price', None)
        if current_price_param:
            try:
                current_price = Decimal(current_price_param)
                if current_price <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                return Response({"error": "Invalid 'current_price' parameter. It must be a positive number."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            current_price = stock.current_price  # from DB

        # 4. FIFO processing: Track each user's "Buy" trades and subtract "Sells"
        user_buy_trades_map = defaultdict(list)  # Maps user_id to list of buy trades

        for tr in trades:
            user_id = tr.user.id
            action = tr.order.action.lower()

            if action == 'buy':
                # Append a buy trade with 'remaining_quantity' initialized
                user_buy_trades_map[user_id].append({
                    "id": tr.id,
                    "user_id": user_id,
                    "username": tr.user.username,
                    "stock_symbol": tr.stock.ticker_symbol,
                    "order_type": tr.order.order_type,
                    "price": tr.price,
                    "quantity": tr.quantity,
                    "transaction_fee": tr.transaction_fee,
                    "trade_time": tr.trade_time,
                    "remaining_quantity": tr.quantity,  # Initialize remaining_quantity
                })
            elif action == 'sell':
                # Process sell trades by reducing from earliest buy trades (FIFO)
                sell_qty = tr.quantity

                if not user_buy_trades_map[user_id]:
                    # User has no buy trades but is trying to sell
                    return Response(
                        {"error": f"User {user_id} has sell trades but no corresponding buy trades."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                buy_trades = user_buy_trades_map[user_id]
                for buy_tr in buy_trades:
                    if buy_tr["remaining_quantity"] <= 0:
                        continue  # Skip fully sold buy trades

                    if buy_tr["remaining_quantity"] >= sell_qty:
                        buy_tr["remaining_quantity"] -= sell_qty
                        sell_qty = 0
                        break  # All sell quantity accounted for
                    else:
                        sell_qty -= buy_tr["remaining_quantity"]
                        buy_tr["remaining_quantity"] = 0

                if sell_qty > 0:
                    # User sold more shares than bought
                    return Response(
                        {"error": f"User {user_id} sold more shares than bought. Data inconsistency."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # 5. Build final list of "Buy" trades with remaining_quantity > 0
        results = []
        for user_id, buy_trades in user_buy_trades_map.items():
            for buy_tr in buy_trades:
                remaining_qty = buy_tr["remaining_quantity"]
                if remaining_qty > 0:
                    trade_date = buy_tr["trade_time"]
                    days_stayed = self.calculate_days_stayed(trade_date)

                    weighted_value = (Decimal(days_stayed) / Decimal(365)) * Decimal(remaining_qty) * current_price
                    weighted_value = weighted_value.quantize(Decimal('0.01'))  # Round to 2 decimal places

                    dividend_eligible = "Yes" if days_stayed >= 10 else "No"

                    total_buying_price = buy_tr["price"] * Decimal(remaining_qty)

                    results.append({
                        "id": buy_tr["id"],
                        "user_id": buy_tr["user_id"],
                        "username": buy_tr["username"],
                        "stock_symbol": buy_tr["stock_symbol"],
                        "order_type": buy_tr["order_type"],
                        "price": f"{buy_tr['price']:.2f}",
                        "quantity": remaining_qty,
                        "transaction_fee": f"{buy_tr['transaction_fee']:.2f}",
                        "trade_time": buy_tr["trade_time"],
                        "total_buying_price": f"{total_buying_price:.2f}",
                        "weighted_value": f"{weighted_value:.2f}",
                        "dividend_eligible": dividend_eligible,
                    })

        # 6. Serialize and return
        serializer = TradeWithOrderInfoOutputSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def calculate_days_stayed(self, trade_date):
        """
        Calculate the number of days from trade_date to June 30 of the current financial year,
        including both the start date and the end date. Logs the result for debugging.
        """
        # Ensure trade_date is timezone-aware
        if timezone.is_naive(trade_date):
            trade_date = make_aware(trade_date, timezone.get_current_timezone())

        # Define end of financial year based on trade_date
        year = trade_date.year
        month = trade_date.month

        if month >= 7:
            fy_end = datetime.datetime(year + 1, 6, 30, tzinfo=datetime.timezone.utc)
        else:
            fy_end = datetime.datetime(year, 6, 30, tzinfo=datetime.timezone.utc)

        # Calculate difference in days and include both start and end dates
        delta = fy_end - trade_date.astimezone(datetime.timezone.utc)
        days_stayed = delta.days + 1  # Add 1 to include both dates

        # Clamp the value between 0 and 365 (financial year limit)
        days_stayed = max(0, min(days_stayed, 365))

        # Log the result
        print(f"Trade Date: {trade_date}, FY End Date: {fy_end}, Days Stayed: {days_stayed}")

        return days_stayed

    
class UserBalancesView(APIView):
    """
    API endpoint to retrieve each user's current balance and holdings.
    Accessible only to admin users.
    """
    #permission_classes = [IsAuthenticated, IsAdminUser]  # Ensure only authenticated admin users can access

    def get(self, request, format=None):
        # Annotate users with total_buy and total_sell
        users = User.objects.annotate(
            total_buy=Sum(
                ExpressionWrapper(
                    F('trades__quantity') * F('trades__price') + F('trades__transaction_fee'),
                    output_field=DecimalField(max_digits=20, decimal_places=2)
                ),
                filter=Q(trades__order__action='Buy')  # Corrected lookup
            ),
            total_sell=Sum(
                ExpressionWrapper(
                    F('trades__quantity') * F('trades__price') - F('trades__transaction_fee'),
                    output_field=DecimalField(max_digits=20, decimal_places=2)
                ),
                filter=Q(trades__order__action='Sell')  # Corrected lookup
            )
        ).all()

        response_data = []

        for user in users:
            total_buy = user.total_buy if user.total_buy else Decimal('0.00')
            total_sell = user.total_sell if user.total_sell else Decimal('0.00')

            # Access account_balance and profit_balance via UserProfile
            if hasattr(user, 'profile'):
                account_balance = user.profile.account_balance
                profit_balance = user.profile.profit_balance
            else:
                account_balance = Decimal('0.00')
                profit_balance = Decimal('0.00')

            # Calculate net balance
            net_balance = account_balance - total_buy + total_sell

            # Calculate holdings per stock
            holdings_queryset = Trade.objects.filter(user_id=user.id).values(
                'stock_id',
                'stock__ticker_symbol'
            ).annotate(
                total_buys=Sum(
                    'quantity',
                    filter=Q(order__action='Buy')
                ),
                total_sells=Sum(
                    'quantity',
                    filter=Q(order__action='Sell')
                )
            ).annotate(
                net_quantity=F('total_buys') - F('total_sells')
            ).filter(net_quantity__gt=0)

            holdings_list = [
                {
                    'stock_id': holding['stock_id'],
                    'stock_symbol': holding['stock__ticker_symbol'],
                    'quantity': holding['net_quantity']
                }
                for holding in holdings_queryset
            ]

            user_data = {
                'user_id': user.id,
                'username': user.username,
                'net_balance': net_balance,
                'holdings': holdings_list
            }

            # Serialize the data
            serialized_user = UserBalanceSerializer(user_data)
            response_data.append(serialized_user.data)

        return Response(response_data, status=200)
    
class DividendDetailedHoldingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet to retrieve the dividend details that were disbursed to each user,
    optionally filtering by company_id and budget_year.
    """
    queryset = DividendDetailedHolding.objects.all().order_by('-created_at')
    serializer_class = DividendDetailedHoldingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        budget_year = self.request.query_params.get('budget_year')
        if company_id:
            qs = qs.filter(company_id=company_id)
        if budget_year:
            qs = qs.filter(budget_year=budget_year)
        return qs
 
# trader's view   
class TraderDividendListView(generics.ListAPIView):
    """
    API endpoint for traders to view their own dividends filtered by budget year.
    """
    serializer_class = TraderDividendSerializer
    permission_classes = [IsAuthenticated, IsTrader]

    def get_queryset(self):
        user = self.request.user
        budget_year = self.request.query_params.get('budget_year')
        queryset = DividendDetailedHolding.objects.filter(user=user)
        if budget_year:
            queryset = queryset.filter(budget_year=budget_year)
        return queryset.order_by('-created_at')

# regulators view
class RegulatorDividendListView(generics.ListAPIView):
    """
    API endpoint for regulators to view all dividends.
    """
    serializer_class = RegulatorDividendSerializer
    permission_classes = [IsAuthenticated, IsRegulator]

    def get_queryset(self):
        budget_year = self.request.query_params.get('budget_year')
        queryset = DividendDetailedHolding.objects.all()
        if budget_year:
            queryset = queryset.filter(budget_year=budget_year)
        return queryset.order_by('-created_at')
    
    

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        Returns a comprehensive dashboard dataset depending on the user's role.
        """
        user = request.user
        role = user.role

        dashboard_data = {
            "user_info": {
                "username": user.username,
                "role": role,
                "account_balance": str(user.account_balance),
                "profit_balance": str(getattr(user, 'profit_balance', 0.00)),
                "date_registered": user.date_registered,
                "last_login": user.last_login,
            },
            "timestamp": now().isoformat()
        }

        # ---- 1. Common data for all roles (e.g., a list of top Stocks, etc.) ----
        # Example: Get top 5 stocks by current_price
        top_stocks = Stocks.objects.order_by('-current_price')[:5]
        top_stocks_data = []
        for stk in top_stocks:
            top_stocks_data.append({
                "ticker_symbol": stk.ticker_symbol,
                "company_name": stk.company.company_name,
                "current_price": str(stk.current_price),
                "available_shares": stk.available_shares,
            })

        dashboard_data["top_stocks"] = top_stocks_data

        # ---- 2. Trader-Specific Data ----
        if role == 'trader':
            # e.g. portfolio summary (already in user.account_balance, but let's do more)
            # Summaries from the user's orders or trades
            total_orders = Orders.objects.filter(user=user).count()
            total_trades = Trade.objects.filter(user=user).count()
            # Could also get the user's portfolio from UsersPortfolio
            try:
                portfolio = UsersPortfolio.objects.get(user=user)
                trader_portfolio = {
                    "quantity": portfolio.quantity,
                    "average_purchase_price": str(portfolio.average_purchase_price),
                    "total_investment": str(portfolio.total_investment),
                }
            except UsersPortfolio.DoesNotExist:
                trader_portfolio = {
                    "quantity": 0,
                    "average_purchase_price": "0.00",
                    "total_investment": "0.00",
                }
            
            # Example aggregator for trader
            dashboard_data["trader_data"] = {
                "total_orders": total_orders,
                "total_trades": total_trades,
                "portfolio": trader_portfolio,
            }

        # ---- 3. Regulator-Specific Data ----
        elif role == 'regulator':
            # e.g. system-wide stats, total number of trades, suspicious activities, etc.
            total_users = User.objects.all().count()
            total_orders = Orders.objects.all().count()
            total_trades = Trade.objects.all().count()
            suspicious_count = SuspiciousActivity.objects.filter(reviewed=False).count()

            # Example aggregator for regulator
            dashboard_data["regulator_data"] = {
                "total_users": total_users,
                "total_orders": total_orders,
                "total_trades": total_trades,
                "pending_suspicious_activities": suspicious_count,
            }

        # ---- 4. Company Admin-Specific Data ----
        elif role == 'company_admin':
            # e.g. fetch the company linked, plus the disclosures or dividends for that company
            if user.company_id:
                # If your approach to linking a company is user.company_id
                user_company_id = user.company_id
                try:
                    company = ListedCompany.objects.get(id=user_company_id)
                    total_stocks = Stocks.objects.filter(company=company).count()
                    # example aggregator
                    admin_info = {
                        "company_name": company.company_name,
                        "company_sector": company.sector,
                        "total_stocks_published": total_stocks,
                    }

                    # maybe list of disclosures
                    disclosures = Disclosure.objects.filter(company=company)
                    admin_info["disclosures_count"] = disclosures.count()

                    # maybe list of dividends for that company
                    dividends = Dividend.objects.filter(company=company)
                    admin_info["dividends_count"] = dividends.count()

                    dashboard_data["company_admin_data"] = admin_info

                except ListedCompany.DoesNotExist:
                    dashboard_data["company_admin_data"] = {
                        "error": "No linked company found for this admin user."
                    }
            else:
                dashboard_data["company_admin_data"] = {
                    "error": "Company admin has no company_id linked."
                }

        else:
            # If role is something else
            dashboard_data["message"] = "No additional dashboard data for this role."

        # Return final aggregated data
        return Response(dashboard_data, status=200)