from django.forms import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Disclosure, UsersPortfolio, ListedCompany, Stocks, Orders, Trade, Dividend
from .serializers import (
    DirectStockPurchaseSerializer,
    DisclosureSerializer,
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
import logging
logger = logging.getLogger(__name__)


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


class StocksViewSet(viewsets.ModelViewSet):
    queryset = Stocks.objects.all()
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

class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer


# views.py snippet:
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
        Retrieve a user's portfolio by their user ID.
        URL: /api/stocks/portfolios/user/<user_id>/
        """
        # Convert user_id to integer and handle potential errors
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
            serializer = self.get_serializer(portfolio)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UsersPortfolio.DoesNotExist:
            return Response(
                {'detail': 'Portfolio not found for the given user ID.'},
                status=status.HTTP_404_NOT_FOUND
            )