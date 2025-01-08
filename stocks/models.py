from decimal import Decimal
from django.db import models, transaction
from django.utils.timezone import timezone, localtime, localdate
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
import logging
from ethio_stock_simulation.utils import send_order_notification
from regulations.models import StockSuspension, calculate_transaction_fee
from regulations.utils import get_regulation_value
from regulations.models import StockSuspension, WorkingHours
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management import call_command
from django.utils.translation import gettext_lazy as _
from django.conf import settings  # To access COMPANY_EMAIL
from django.core.mail import send_mail  # To send emails
from stocks.models_audit import TransactionAuditTrail
from stocks.utils import is_within_working_hours
from .models_suspicious import SuspiciousActivity  # Import here to include the model



# Configure logging
logger = logging.getLogger(__name__)
User = get_user_model()

class UsersPortfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    quantity = models.IntegerField(default=0)
    average_purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Portfolio of {self.user.username}"


class ListedCompany(models.Model):
    company_name = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    order = models.ForeignKey('Orders', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    trade = models.ForeignKey('Trade', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.order:
            return f"Notification for Order {self.order.id}: {self.message[:50]}"
        elif self.trade:
            return f"Notification for Trade {self.trade.id}: {self.message[:50]}"
        return f"Notification for {self.user.username}: {self.message[:50]}"
    
class Stocks(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='stocks')
    ticker_symbol = models.CharField(max_length=10, unique=True)
    total_shares = models.IntegerField()
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    available_shares = models.IntegerField()
    max_trader_buy_limit = models.IntegerField(default=1000)  # Maximum shares a trader can buy directly from the company
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ticker_symbol} ({self.company.company_name})"

    def clean(self):
        # Ensure max_trader_buy_limit does not exceed available shares
        if self.max_trader_buy_limit > self.total_shares:
            raise ValueError("Trader buy limit cannot exceed the total shares of the company.")

    @classmethod
    def execute_direct_purchase(cls, user_id, stock_id, quantity):
        """
        Executes a direct stock purchase for a user.

        Args:
            user_id (int): ID of the user making the purchase.
            stock_id (int): ID of the stock to purchase.
            quantity (int): Number of shares to purchase.

        Returns:
            tuple: (order, trade_buyer) instances created.

        Raises:
            ValidationError: If any validation fails.
        """
        TRANSACTION_FEE_PERCENTAGE = Decimal('0.01')  # 1%

        with transaction.atomic():
            try:
                # Lock the user record for update to prevent race conditions
                user = User.objects.select_for_update().get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User with ID {user_id} does not exist.")
                raise ValidationError("Invalid user ID.")

            try:
                # Lock the stock record for update to prevent race conditions
                stock = cls.objects.select_for_update().get(id=stock_id)
            except cls.DoesNotExist:
                logger.error(f"Stock with ID {stock_id} does not exist.")
                raise ValidationError("Invalid stock ID.")

            # Validate purchase quantity against max trader buy limit
            if quantity > stock.max_trader_buy_limit:
                logger.warning(
                    f"User {user_id} attempted to buy {quantity} shares, exceeding the max limit of {stock.max_trader_buy_limit}."
                )
                raise ValidationError(
                    f"Cannot buy more than {stock.max_trader_buy_limit} shares directly."
                )

            # Validate available shares
            if stock.available_shares < quantity:
                logger.warning(
                    f"User {user_id} attempted to buy {quantity} shares, but only {stock.available_shares} are available."
                )
                raise ValidationError("Insufficient shares available from the company.")

            # Check if current time is within working hours
            current_time = timezone.now()
            if not is_within_working_hours(current_time):
                logger.warning(
                    f"User {user_id} attempted to buy shares outside of working hours."
                )
                raise ValidationError("Cannot place orders outside of working hours.")

            # Calculate total cost
            total_cost = Decimal(quantity) * stock.current_price

            # Calculate transaction fee
            transaction_fee = (total_cost * TRANSACTION_FEE_PERCENTAGE).quantize(Decimal('0.01'))

            # Total amount to be deducted (cost + fee)
            total_amount = total_cost + transaction_fee

            # Validate user's account balance
            if user.account_balance < total_amount:
                logger.warning(
                    f"User {user_id} has insufficient balance. Required: {total_amount}, Available: {user.account_balance}."
                )
                raise ValidationError("Insufficient account balance to complete the purchase, including transaction fees.")

            # Deduct total amount from user's account balance
            user.account_balance -= total_amount
            user.save()

            # Create the order with 'direct_purchase=True' to bypass matching logic
            order = Orders(
                user=user,
                stock=stock,
                stock_symbol=stock.ticker_symbol,
                order_type='Market',
                action='Buy',
                price=stock.current_price,
                quantity=quantity,
                status='Fully Completed',  # Direct purchases are immediately completed
                transaction_fee=transaction_fee,
            )
            order.save(direct_purchase=True)  # Pass the flag here

            # Execute the trade via Trade.execute_trade
            trade_buyer, trade_seller = Trade.execute_trade(
                buy_order=order,
                sell_order=None,  # None indicates company is the seller
                quantity=quantity,
                price=stock.current_price
            )

            # Update user portfolio
            portfolio, created = UsersPortfolio.objects.select_for_update().get_or_create(user=user)
            portfolio.quantity += quantity
            portfolio.total_investment += total_cost
            if portfolio.quantity > 0:
                portfolio.average_purchase_price = (
                    portfolio.total_investment / portfolio.quantity
                ).quantize(Decimal('0.01'))
            portfolio.save()

            # Update stock's available shares
            stock.available_shares -= quantity
            stock.save()

            # The audit trail is handled within Trade.execute_trade, so no need to duplicate here

            logger.info(
                f"User {user_id} successfully purchased {quantity} shares of {stock.ticker_symbol} "
                f"for a total of {total_cost} with a transaction fee of {transaction_fee}. "
                f"New balance: {user.account_balance}."
            )

            return order, trade_buyer  # Return the order and buyer's Trade instance
        
        
class Orders(models.Model):
    ORDER_TYPE_CHOICES = [
        ('Market', 'Market'),
        ('Limit', 'Limit'),
    ]
    ACTION_CHOICES = [
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Completed', 'Partially Completed'),
        ('Fully Completed', 'Fully Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    stock = models.ForeignKey('stocks.Stocks', on_delete=models.CASCADE, related_name='orders')
    stock_symbol = models.CharField(max_length=10)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField()
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['stock', 'action', 'price', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.action} Order for {self.stock_symbol}"

    def save(self, *args, **kwargs):
        # Extract the 'direct_purchase' flag if provided; default to False
        direct_purchase = kwargs.pop('direct_purchase', False)

        is_new = self._state.adding

        # Perform validations regardless of direct_purchase flag
        # 1. Check for active stock suspensions
        stock_suspension = StockSuspension.objects.filter(
            trader=self.user, stock=self.stock, is_active=True, suspension_type='Specific Stock'
        ).exists()

        global_suspension = StockSuspension.objects.filter(
            trader=self.user, is_active=True, suspension_type='All Stocks'
        ).exists()

        if stock_suspension or global_suspension:
            raise ValidationError("Trading for this user is suspended.")

        # 2. Check working hours using WorkingHours table
        current_time = localtime()
        if not is_within_working_hours(current_time):
            raise ValidationError("Orders can only be created during working hours.")

        # 3. Check daily trade limit (if applicable)
        daily_trade_limit = get_regulation_value("Daily Trade Limit")
        if daily_trade_limit:
            user_trades_today = Orders.objects.filter(
                user=self.user, created_at__date=localdate()
            ).count()
            if user_trades_today >= int(daily_trade_limit):
                raise ValidationError("Daily trade limit reached.")

        # 4. Ensure the user has a portfolio
        portfolio, created = UsersPortfolio.objects.get_or_create(
            user=self.user,
            defaults={
                'quantity': 0,
                'average_purchase_price': Decimal('0.00'),
                'total_investment': Decimal('0.00'),
            }
        )

        # 5. Validate Buy Order: Ensure sufficient account balance
        if self.action == 'Buy':
            if self.price is None:
                raise ValidationError("Price must be set for Buy orders.")
            total_cost = Decimal(self.price) * Decimal(self.quantity)
            if self.user.account_balance < total_cost:
                raise ValidationError("Insufficient account balance to place a buy order.")

        # 6. Validate Sell Order: Ensure sufficient stock ownership
        if self.action == 'Sell':
            owned_quantity = Trade.objects.filter(
                user=self.user,
                stock=self.stock,
            ).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0

            if owned_quantity < self.quantity:
                raise ValidationError("You do not own enough stock to place this sell order.")

        # 7. Set order status based on direct_purchase flag
        if is_new and not direct_purchase:
            self.status = 'Pending'

        # Save the order
        super().save(*args, **kwargs)

        if is_new:
            if direct_purchase:
                # For direct purchases, do not create 'OrderCreated' audit trail
                # The audit trail is handled in Trade.execute_trade
                pass
            else:
                # Log audit trail for regular order creation
                TransactionAuditTrail.objects.create(
                    event_type='OrderCreated',
                    order=self,
                    trade=None,
                    details=(
                        f"New order created. Action: {self.action}, Type: {self.order_type}, "
                        f"Quantity: {self.quantity}, Price: {self.price}, Status: {self.status}"
                    )
                )
                # Execute matching logic
                Orders.match_and_execute_orders(self)

    @classmethod
    def match_and_execute_orders(cls, new_order):
        with transaction.atomic():
            if new_order.action == 'Buy':
                cls._handle_buy_order(new_order)
            elif new_order.action == 'Sell':
                cls._handle_sell_order(new_order)

    @classmethod
    def _handle_buy_order(cls, buy_order):
        """
        Handles the execution of Buy orders based on order type and price-time priority.
        """
        stock = buy_order.stock

        # Step 1: Handle Market Orders
        if buy_order.order_type == 'Market':
            # Attempt to buy from the company first
            available_shares = stock.available_shares
            if available_shares > 0:
                trade_quantity = min(buy_order.quantity, available_shares)
                trade_price = stock.current_price  # Company's current price

                # Execute the trade with the company
                trade_buyer, trade_seller = Trade.execute_trade(buy_order, None, trade_quantity, trade_price)

                # Update stock
                stock.available_shares -= trade_quantity
                stock.save()

                # Update order quantity and status
                buy_order.quantity -= trade_quantity
                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'
                buy_order.save()

                # No need to log audit trail here as it's handled in Trade.execute_trade

        # Step 2: Handle Limit Orders
        elif buy_order.order_type == 'Limit':
            # Step 2.1: Check if company has available stock at or below Buy Limit Order's price
            available_shares = stock.available_shares
            if available_shares > 0 and stock.current_price <= buy_order.price:
                trade_quantity = min(buy_order.quantity, available_shares)
                trade_price = stock.current_price  # Company's current price

                # Execute the trade with the company
                trade_buyer, trade_seller = Trade.execute_trade(buy_order, None, trade_quantity, trade_price)

                # Update stock
                stock.available_shares -= trade_quantity
                stock.save()

                # Update order quantity and status
                buy_order.quantity -= trade_quantity
                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'
                buy_order.save()

                # No need to log audit trail here as it's handled in Trade.execute_trade

        # Step 3: Attempt to buy remaining shares from other traders' sell orders
        if buy_order.quantity > 0:
            if buy_order.order_type == 'Market':
                # Fetch Sell Orders priced at or below Buy Market Order's price (company's price)
                sell_orders = cls.objects.filter(
                    stock=stock,
                    action='Sell',
                    status='Pending',
                    is_direct_purchase=False  # Ensure it's not a direct purchase
                ).order_by('price', 'created_at')  # Lowest price first, earliest order next
            elif buy_order.order_type == 'Limit':
                # Fetch Sell Limit Orders priced at or below Buy Limit Order's price
                sell_orders = cls.objects.filter(
                    stock=stock,
                    action='Sell',
                    status='Pending',
                    price__lte=buy_order.price,
                    is_direct_purchase=False  # Ensure it's not a direct purchase
                ).order_by('price', 'created_at')  # Lowest price first, earliest order next

            for sell_order in sell_orders:
                if buy_order.quantity == 0:
                    break

                trade_quantity = min(buy_order.quantity, sell_order.quantity)
                trade_price = sell_order.price  # Sell Order's price

                # Execute the trade
                trade_buyer, trade_seller = Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                # Adjust quantities and statuses
                buy_order.quantity -= trade_quantity
                sell_order.quantity -= trade_quantity

                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'

                if sell_order.quantity == 0:
                    sell_order.status = 'Fully Completed'
                else:
                    sell_order.status = 'Partially Completed'

                buy_order.save()
                sell_order.save()

                # No need to log audit trail here as it's handled in Trade.execute_trade

    @classmethod
    def _handle_sell_order(cls, sell_order):
        """
        Handles the execution of Sell orders based on order type and price-time priority.
        """
        stock = sell_order.stock

        # Step 1: Validate sufficient stock ownership
        total_owned_quantity = Trade.objects.filter(
            user=sell_order.user,
            stock=stock
        ).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0

        if total_owned_quantity < sell_order.quantity:
            sell_order.status = 'Cancelled'
            sell_order.save()
            # Log audit trail for cancellation
            TransactionAuditTrail.objects.create(
                event_type='OrderStatusChanged',
                order=sell_order,
                trade=None,
                details={
                    'reason': 'Insufficient stock ownership',
                    'requested_quantity': sell_order.quantity,
                    'owned_quantity': total_owned_quantity,
                }
            )
            raise ValidationError("Insufficient stock to sell.")

        with transaction.atomic():
            if sell_order.order_type == 'Market':
                # Attempt to match with existing Buy Orders (highest price first, earliest order next)
                buy_orders = cls.objects.filter(
                    stock=stock,
                    action='Buy',
                    status='Pending',
                    is_direct_purchase=False  # Ensure it's not a direct purchase
                ).order_by('-price', 'created_at')  # Highest price first, earliest order next

                for buy_order in buy_orders:
                    if sell_order.quantity == 0:
                        break

                    # Determine trade price
                    if buy_order.order_type == 'Limit':
                        trade_price = buy_order.price
                    else:  # Buy Market Order
                        trade_price = stock.current_price

                    trade_quantity = min(sell_order.quantity, buy_order.quantity)

                    # Execute the trade
                    trade_buyer, trade_seller = Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                    # Adjust quantities and statuses
                    sell_order.quantity -= trade_quantity
                    buy_order.quantity -= trade_quantity

                    if sell_order.quantity == 0:
                        sell_order.status = 'Fully Completed'
                    else:
                        sell_order.status = 'Partially Completed'

                    if buy_order.quantity == 0:
                        buy_order.status = 'Fully Completed'
                    else:
                        buy_order.status = 'Partially Completed'

                    sell_order.save()
                    buy_order.save()

                    # No need to log audit trail here as it's handled in Trade.execute_trade

            elif sell_order.order_type == 'Limit':
                # Attempt to match with existing Buy Limit Orders priced at or above the Sell Order's price
                buy_orders = cls.objects.filter(
                    stock=stock,
                    action='Buy',
                    status='Pending',
                    price__gte=sell_order.price,
                    is_direct_purchase=False  # Ensure it's not a direct purchase
                ).order_by('-price', 'created_at')  # Highest price first, earliest order next

                for buy_order in buy_orders:
                    if sell_order.quantity == 0:
                        break

                    trade_quantity = min(sell_order.quantity, buy_order.quantity)
                    trade_price = buy_order.price  # Execute at Buy Order's price

                    # Execute the trade
                    trade_buyer, trade_seller = Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                    # Adjust quantities and statuses
                    sell_order.quantity -= trade_quantity
                    buy_order.quantity -= trade_quantity

                    if sell_order.quantity == 0:
                        sell_order.status = 'Fully Completed'
                    else:
                        sell_order.status = 'Partially Completed'

                    if buy_order.quantity == 0:
                        buy_order.status = 'Fully Completed'
                    else:
                        buy_order.status = 'Partially Completed'

                    sell_order.save()
                    buy_order.save()

                    # No need to log audit trail here as it's handled in Trade.execute_trade

        # Note: Orders remain 'Pending' until end-of-day processing for any unfulfilled quantities
    @staticmethod
    def _update_portfolio(user, stock, quantity, price, is_buy):
        """
        Updates the user's portfolio based on the trade.
        This method is invoked after trade execution.
        """
        with transaction.atomic():
            portfolio = UsersPortfolio.objects.select_for_update().get_or_create(user=user)[0]
            quantity = Decimal(quantity)
            price = Decimal(price)

            if is_buy:
                portfolio.quantity += quantity
                portfolio.total_investment += quantity * price
                if portfolio.quantity > 0:
                    portfolio.average_purchase_price = portfolio.total_investment / portfolio.quantity
            else:  # Sell
                portfolio.quantity -= quantity
                portfolio.total_investment -= quantity * price
                if portfolio.quantity > 0:
                    portfolio.average_purchase_price = portfolio.total_investment / portfolio.quantity
                else:
                    portfolio.average_purchase_price = Decimal('0.00')  # Reset if no stocks remain

            portfolio.save()

def notify_user_real_time(user, message):
    """
    Sends a real-time notification to the user using Django Channels.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": {"content": message},
        }
    )
class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='trades')
    order = models.ForeignKey('Orders', on_delete=models.CASCADE, related_name='trades', null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    trade_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Trade by {self.user.username} on {self.trade_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def execute_trade(cls, buy_order, sell_order, quantity, price=None):
        """
        Executes a trade between a buy order and a sell order.
        Applies transaction fees, updates account balances, logs audit trails,
        and sends notifications to both buyer and seller.

        Args:
            buy_order (Orders): The buy order involved in the trade.
            sell_order (Orders or None): The sell order involved in the trade.
                None if it's a direct purchase from the company.
            quantity (int): Number of shares to trade.
            price (Decimal or None): Price per share. If None, determined based on order types.

        Returns:
            tuple: (trade_buyer, trade_seller) instances created.
                If sell_order is None, trade_seller is None.
        """
        if price is None:
            if sell_order:
                price = sell_order.stock.current_price
            else:
                price = buy_order.stock.current_price

        # Calculate transaction fees
        TRANSACTION_FEE_PERCENTAGE = Decimal('0.01')  # 1%
        total_cost = Decimal(quantity) * Decimal(price)
        transaction_fee_buyer = (total_cost * TRANSACTION_FEE_PERCENTAGE).quantize(Decimal('0.01'))

        with transaction.atomic():
            # Create trade entry for the buyer
            trade_buyer = cls.objects.create(
                user=buy_order.user,
                stock=buy_order.stock,
                order=buy_order,
                quantity=quantity,
                price=price,
                transaction_fee=transaction_fee_buyer
            )

            # Deduct total_cost and transaction_fee from buyer's account balance
            buy_order.user.account_balance -= (total_cost + transaction_fee_buyer)
            buy_order.user.save()

            # Update order's transaction_fee
            buy_order.transaction_fee += transaction_fee_buyer
            buy_order.save()

            # Determine seller details
            if sell_order:
                seller_user = sell_order.user
                seller_email = seller_user.email
                seller_username = seller_user.username
            else:
                # Seller is the company
                seller_user = None
                seller_email = settings.COMPANY_EMAIL
                seller_username = buy_order.stock.company.company_name

            # Create audit trail for buyer's trade
            TransactionAuditTrail.objects.create(
                event_type='TradeExecuted',
                order=buy_order,
                trade=trade_buyer,
                details={
                    'trade_type': 'Buyer',
                    'buyer_id': buy_order.user.id,
                    'buyer_username': buy_order.user.username,
                    'seller_id': seller_user.id if seller_user else None,
                    'seller_username': seller_username,
                    'stock_id': buy_order.stock.id,
                    'stock_symbol': buy_order.stock.ticker_symbol,
                    'quantity': quantity,
                    'price_per_share': str(price),
                    'total_cost': str(total_cost),
                    'transaction_fee': str(transaction_fee_buyer),
                    'remaining_quantity': buy_order.quantity if buy_order.status != 'Fully Completed' else 0
                }
            )

            trade_seller = None
            if sell_order:
                # Calculate seller's transaction fee
                transaction_fee_seller = (total_cost * TRANSACTION_FEE_PERCENTAGE).quantize(Decimal('0.01'))

                # Create trade entry for the seller
                trade_seller = cls.objects.create(
                    user=sell_order.user,
                    stock=sell_order.stock,
                    order=sell_order,
                    quantity=quantity,
                    price=price,
                    transaction_fee=transaction_fee_seller
                )

                # Credit total_cost and deduct transaction_fee from seller's account balance
                sell_order.user.account_balance += (total_cost - transaction_fee_seller)
                sell_order.user.save()

                # Update sell order's transaction_fee
                sell_order.transaction_fee += transaction_fee_seller
                sell_order.save()

                # Create audit trail for seller's trade
                TransactionAuditTrail.objects.create(
                    event_type='TradeExecuted',
                    order=sell_order,
                    trade=trade_seller,
                    details={
                        'trade_type': 'Seller',
                        'buyer_id': buy_order.user.id,
                        'buyer_username': buy_order.user.username,
                        'seller_id': sell_order.user.id,
                        'seller_username': sell_order.user.username,
                        'stock_id': sell_order.stock.id,
                        'stock_symbol': sell_order.stock.ticker_symbol,
                        'quantity': quantity,
                        'price_per_share': str(price),
                        'total_proceeds': str(total_cost),
                        'transaction_fee': str(transaction_fee_seller),
                        'remaining_quantity': sell_order.quantity if sell_order.status != 'Fully Completed' else 0
                    }
                )

                # Detect suspicious trades for both buyer and seller
                SuspiciousActivity.detect_suspicious_trade(trade_buyer)
                SuspiciousActivity.detect_suspicious_trade(trade_seller)

                # Send notifications to both buyer and seller
                send_order_notification(
                    to_email=buy_order.user.email,
                    username=buy_order.user.username,
                    action="Buy",
                    stock_symbol=buy_order.stock.ticker_symbol,
                    quantity=quantity,
                    price=price,
                    new_balance=buy_order.user.account_balance
                )

                send_order_notification(
                    to_email=sell_order.user.email,
                    username=sell_order.user.username,
                    action="Sell",
                    stock_symbol=sell_order.stock.ticker_symbol,
                    quantity=quantity,
                    price=price,
                    new_balance=sell_order.user.account_balance
                )
            else:
                # For direct purchases from the company, notify only the buyer
                send_order_notification(
                    to_email=buy_order.user.email,
                    username=buy_order.user.username,
                    action="Buy",
                    stock_symbol=buy_order.stock.ticker_symbol,
                    quantity=quantity,
                    price=price,
                    new_balance=buy_order.user.account_balance
                )

            return trade_buyer, trade_seller  # Return both trades
        
    def send_trade_notifications(buyer, seller, stock_symbol, quantity, price, transaction_fee_buyer, transaction_fee_seller, total_cost, total_proceeds, remaining_quantity_buyer, remaining_quantity_seller):
        """
        Sends trade notifications to both buyer and seller.

        Args:
            buyer (User): Buyer user instance.
            seller (User): Seller user instance.
            stock_symbol (str): Stock ticker symbol.
            quantity (int): Number of shares traded.
            price (Decimal): Price per share.
            transaction_fee_buyer (Decimal): Transaction fee for buyer.
            transaction_fee_seller (Decimal): Transaction fee for seller.
            total_cost (Decimal): Total cost of the trade.
            total_proceeds (Decimal): Total proceeds from the trade.
            remaining_quantity_buyer (int): Remaining quantity in buyer's order.
            remaining_quantity_seller (int): Remaining quantity in seller's order.
        """
        # Prepare buyer email content
        buyer_subject = f"Trade Confirmation for {stock_symbol}"
        buyer_message = (
            f"Dear {buyer.username},\n\n"
            f"Your purchase of {quantity} shares of {stock_symbol} at {price} per share has been executed.\n"
            f"Transaction Fee: {transaction_fee_buyer}\n"
            f"Total Cost: {total_cost} + Transaction Fee: {transaction_fee_buyer} = {total_cost + transaction_fee_buyer}\n"
            f"Remaining Quantity: {remaining_quantity_buyer}\n\n"
            f"Thank you for trading with us."
        )

        # Prepare seller email content
        seller_subject = f"Trade Confirmation for {stock_symbol}"
        seller_message = (
            f"Dear {seller.username},\n\n"
            f"Your sale of {quantity} shares of {stock_symbol} at {price} per share has been executed.\n"
            f"Transaction Fee: {transaction_fee_seller}\n"
            f"Total Proceeds: {total_proceeds} - Transaction Fee: {transaction_fee_seller} = {total_proceeds - transaction_fee_seller}\n"
            f"Remaining Quantity: {remaining_quantity_seller}\n\n"
            f"Thank you for trading with us."
        )

        # Send emails
        send_mail(
            subject=buyer_subject,
            message=buyer_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[buyer.email],
            fail_silently=False,
        )

        send_mail(
            subject=seller_subject,
            message=seller_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[seller.email],
            fail_silently=False,
        )

def send_direct_purchase_notification(buyer, company_name, stock_symbol, quantity, price, transaction_fee, total_cost, total_deducted, remaining_quantity):
    """
    Sends a direct purchase notification to the buyer.

    Args:
        buyer (User): Buyer user instance.
        company_name (str): Name of the company selling the stock.
        stock_symbol (str): Stock ticker symbol.
        quantity (int): Number of shares purchased.
        price (Decimal): Price per share.
        transaction_fee (Decimal): Transaction fee for the buyer.
        total_cost (Decimal): Total cost of the trade.
        total_deducted (Decimal): Total amount deducted from buyer's account.
        remaining_quantity (int): Remaining quantity in buyer's order.
    """
    subject = f"Direct Purchase Confirmation for {stock_symbol}"
    message = (
        f"Dear {buyer.username},\n\n"
        f"Your direct purchase of {quantity} shares of {stock_symbol} from {company_name} at {price} per share has been executed.\n"
        f"Transaction Fee: {transaction_fee}\n"
        f"Total Cost: {total_cost} + Transaction Fee: {transaction_fee} = {total_deducted}\n"
        f"Remaining Quantity: {remaining_quantity}\n\n"
        f"Thank you for trading with us."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[buyer.email],
        fail_silently=False,
    )

class Dividend(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='dividends')
    budget_year = models.CharField(max_length=4)
    dividend_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    total_dividend_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=15, choices=[('Paid', 'Paid'), ('Pending', 'Pending')], default='Pending')

    def __str__(self):
        return f"Dividend for {self.company.company_name} ({self.budget_year})"


class DailyClosingPrice(models.Model):
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='daily_closes')
    date = models.DateField(auto_now_add=True)
    closing_price = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.stock.ticker_symbol} closing price on {self.date}: {self.closing_price}"  

class Disclosure(models.Model):
    """
    Disclosure model for storing documents like financial statements, annual reports, etc.
    """

    class DisclosureTypes(models.TextChoices):
        FINANCIAL_STATEMENT = 'Financial Statement', _('Financial Statement')
        ANNUAL_REPORT       = 'Annual Report', _('Annual Report')
        MATERIAL_EVENT      = 'Material Event', _('Material Event')
        QUARTERLY_REPORT    = 'Quarterly Report', _('Quarterly Report')

    company = models.ForeignKey(
        ListedCompany,
        on_delete=models.CASCADE,
        related_name='disclosures',
        help_text=_("Company to which this disclosure belongs.")
    )
    # Using 'disclosure_type' is often safer than using the reserved word 'type'.
    type = models.CharField(
        max_length=50,
        choices=DisclosureTypes.choices,
        help_text=_("Type of disclosure (e.g., 'Financial Statement', 'Annual Report').")
    )
    year = models.PositiveIntegerField(
        help_text=_("Fiscal or reporting year for this disclosure.")
    )
    file = models.FileField(
        upload_to='disclosures/',
        help_text=_("File containing disclosure document.")
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Optional description or summary of the disclosure.")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp indicating when this disclosure was uploaded.")
    )

    class Meta:
        ordering = ['-year', '-uploaded_at']
        verbose_name = "Disclosure"
        verbose_name_plural = "Disclosures"

    def __str__(self):
        return f"{self.get_disclosure_type_display()} ({self.year}) - {self.company.name}"

