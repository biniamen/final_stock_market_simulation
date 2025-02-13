from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.utils.timezone import localtime, localdate
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
import logging
from django.db.models import Sum, F

# Adjust these imports based on your project structure
from ethio_stock_simulation.utils import send_order_notification
from regulations.models import StockSuspension
from regulations.utils import get_regulation_value
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from stocks.models_audit import TransactionAuditTrail
from stocks.utils import is_within_working_hours
from .surveillance import detect_suspicious_trade

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
    order = models.ForeignKey(
        'Orders',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    trade = models.ForeignKey(
        'Trade',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
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
    max_trader_buy_limit = models.IntegerField(default=1000)  # Max shares a trader can buy from the company directly
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ticker_symbol} ({self.company.company_name})"

    def clean(self):
        # Ensure max_trader_buy_limit does not exceed total_shares
        if self.max_trader_buy_limit > self.total_shares:
            raise ValidationError("Trader buy limit cannot exceed the total shares of the company.")

    @classmethod
    def execute_direct_purchase(cls, user_id, stock_id, quantity):
        """
        Executes a direct purchase from the company stock (bypassing matching).
        """
        TRANSACTION_FEE_PERCENTAGE = Decimal('0.01')  # 1%

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User with ID {user_id} does not exist.")
                raise ValidationError("Invalid user ID.")

            try:
                stock = cls.objects.select_for_update().get(id=stock_id)
            except cls.DoesNotExist:
                logger.error(f"Stock with ID {stock_id} does not exist.")
                raise ValidationError("Invalid stock ID.")

            # Validate quantity vs. max_trader_buy_limit
            if quantity > stock.max_trader_buy_limit:
                logger.warning(
                    f"User {user_id} attempted to buy {quantity} shares, exceeding limit of {stock.max_trader_buy_limit}."
                )
                raise ValidationError(f"Cannot buy more than {stock.max_trader_buy_limit} shares directly.")

            # Check available shares
            if stock.available_shares < quantity:
                logger.warning(
                    f"User {user_id} tried to buy {quantity}, but only {stock.available_shares} available."
                )
                raise ValidationError("Insufficient shares available from the company.")

            # Check if current time is within working hours
            current_time = timezone.now()
            if not is_within_working_hours(current_time):
                logger.warning(f"User {user_id} tried to buy outside working hours.")
                raise ValidationError("Cannot place orders outside of working hours.")

            # Calculate cost and fee
            total_cost = Decimal(quantity) * stock.current_price
            transaction_fee = (total_cost * TRANSACTION_FEE_PERCENTAGE).quantize(Decimal('0.01'))
            total_amount = total_cost + transaction_fee

            # Check user account balance
            if user.account_balance < total_amount:
                logger.warning(
                    f"User {user_id} has insufficient balance. Required {total_amount}, available {user.account_balance}."
                )
                raise ValidationError("Insufficient account balance to complete purchase and fees.")

            # Create the order with 'direct_purchase=True' to skip matching
            order = Orders(
                user=user,
                stock=stock,
                stock_symbol=stock.ticker_symbol,
                order_type='Market',
                action='Buy',
                price=stock.current_price,
                quantity=quantity,
                status='Fully Completed',
                transaction_fee=transaction_fee,
            )
            order.save(direct_purchase=True)

            # Execute the trade (None => company is the seller)
            trade_buyer, trade_seller = Trade.execute_trade(
                buy_order=order,
                sell_order=None,
                quantity=quantity,
                price=stock.current_price
            )

            # Update stock's available_shares
            stock.available_shares -= quantity
            stock.save()

            logger.info(
                f"User {user_id} purchased {quantity} shares of {stock.ticker_symbol} for {total_cost}, fee {transaction_fee}."
            )

            return order, trade_buyer


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
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='orders')
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
        """
        If direct_purchase=True, skip matching logic.
        Otherwise, handle normal validations and possibly match_and_execute_orders.
        """
        direct_purchase = kwargs.pop('direct_purchase', False)
        is_new = self._state.adding

        if is_new:
            # Perform basic checks
            self._perform_basic_checks(direct_purchase)

        # Save the order to DB
        super().save(*args, **kwargs)

        if is_new:
            if direct_purchase:
                # Bypass all matching logic
                logger.debug("Direct purchase order created; skipping matching logic.")
            else:
                # Log audit for normal orders
                TransactionAuditTrail.objects.create(
                    event_type='OrderCreated',
                    order=self,
                    trade=None,
                    details=(
                        f"New order created. Action: {self.action}, "
                        f"Type: {self.order_type}, Quantity: {self.quantity}, "
                        f"Price: {self.price}, Status: {self.status}"
                    )
                )
                # Execute matching
                Orders.match_and_execute_orders(self)

    def _perform_basic_checks(self, direct_purchase=False):
        """
        Basic validations: suspensions, working hours, daily trade limit,
        portfolio existence, buy/sell constraints, daily trade amount limit, etc.
        """
        # 1. Check suspensions
        if StockSuspension.objects.filter(
            trader=self.user, stock=self.stock, is_active=True, suspension_type='Specific Stock'
        ).exists() or StockSuspension.objects.filter(
            trader=self.user, is_active=True, suspension_type='All Stocks'
        ).exists():
            raise ValidationError("Trading for this user is suspended.")

        # 2. Working hours (only for normal orders)
        if not direct_purchase:
            current_time = localtime()
            if not is_within_working_hours(current_time):
                raise ValidationError("Orders can only be created during working hours.")

        # 3. Daily trade (count) limit
        daily_trade_limit = get_regulation_value("Daily Trade Limit")
        if daily_trade_limit:
            user_trades_today = Orders.objects.filter(
                user=self.user, created_at__date=localdate()
            ).count()
            if user_trades_today >= int(daily_trade_limit):
                raise ValidationError("Daily trade limit reached.")

        # -----------------------------
        # 3.1. Daily trade AMOUNT limit
        # -----------------------------
        # Suppose you store the numeric limit in the regulation as a string or decimal.
        daily_trade_amount_limit = get_regulation_value("Daily Trade Amount Limit")
        if daily_trade_amount_limit:
            # Convert string to Decimal if needed
            daily_trade_amount_limit = Decimal(daily_trade_amount_limit)

            # Sum up the user's total traded amount for the current day.
            # Here, we consider *all* trades or just *buy* trades, depending on your rule.
            # Example 1: Summing *all* trades (buy + sell).
            user_trades_today_amount = Trade.objects.filter(
                user=self.user,
                trade_time__date=localdate()  # trades made today
            ).aggregate(
                total_amount=Sum(F('quantity') * F('price'))
            )['total_amount'] or Decimal('0.00')

            # OR Example 2: Summing *only buy* trades
            # user_trades_today_amount = Trade.objects.filter(
            #     user=self.user,
            #     order__action='Buy',  # only Buy side
            #     trade_time__date=localdate()
            # ).aggregate(
            #     total_amount=Sum(F('quantity') * F('price'))
            # )['total_amount'] or Decimal('0.00')

            # We'll calculate the cost of this new order:
            # For a Buy order:
            if self.action == 'Buy':
                # For a Market Buy, use stock.current_price if self.price is None
                if self.price is None:
                    stock_price = self.stock.current_price or Decimal('0.00')
                else:
                    stock_price = self.price
                new_order_cost = stock_price * self.quantity

                # Check if adding this cost to what the user has already traded exceeds the limit.
                if (user_trades_today_amount + new_order_cost) > daily_trade_amount_limit:
                    raise ValidationError("Daily trade amount limit reached.")

            # If you also want to restrict sells by the *proceeds* of the sell, or treat them
            # as part of a total volume, do something similar for `self.action == 'Sell'`.
            # For a Sell order, "amount" might be (sell_price * quantity). 
            # Adjust to your business logic:
            if self.action == 'Sell':
                # Suppose you also want to count sells toward the daily volume:
                if self.order_type == 'Limit' and self.price is not None:
                    potential_sell_amount = self.price * self.quantity
                else:
                    # For a Market Sell, might use stock.current_price
                    potential_sell_amount = self.stock.current_price * self.quantity

                if (user_trades_today_amount + potential_sell_amount) > daily_trade_amount_limit:
                    raise ValidationError("Daily trade amount limit reached.")
        # -----------------------------

        # 4. Ensure portfolio exists
        portfolio, created = UsersPortfolio.objects.get_or_create(
            user=self.user,
            defaults={
                'quantity': 0,
                'average_purchase_price': Decimal('0.00'),
                'total_investment': Decimal('0.00'),
            }
        )

        # 5. Validate Buy Orders
        if self.action == 'Buy':
            # For limit buy, ensure price is not None
            if self.order_type == 'Limit' and self.price is None:
                raise ValidationError("Price must be set for Limit Buy orders.")

            # If not direct_purchase, check user.account_balance
            if not direct_purchase:
                if self.price is None:
                    # For Market Buy, assume stock.current_price
                    stock_price = self.stock.current_price or Decimal('0.00')
                else:
                    stock_price = self.price
                total_cost = stock_price * self.quantity
                if self.user.account_balance < total_cost:
                    raise ValidationError("Insufficient account balance to place a buy order.")

        # 6. Validate Sell Orders
        if self.action == 'Sell':
            owned_quantity = Trade.objects.filter(
                user=self.user,
                stock=self.stock,
            ).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0
            if owned_quantity < self.quantity:
                raise ValidationError("You do not own enough stock to place this sell order.")

    @classmethod
    def match_and_execute_orders(cls, new_order):
        """Entry point to match buy/sell orders based on type & price-time priority."""
        with transaction.atomic():
            if new_order.action == 'Buy':
                cls._handle_buy_order(new_order)
            else:  # Sell
                cls._handle_sell_order(new_order)

    @classmethod
    def _handle_buy_order(cls, buy_order):
        """Process Market/Limit Buy: partial fill from pending/partially completed Sell orders, then match remaining with company."""
        stock = buy_order.stock

        # 1. Match with existing Sell Orders
        # -- STATUS CORRECTION: we look for sell orders with status in ['Pending', 'Partially Completed'].
        if buy_order.order_type == 'Market':
            # No price limit from buyer side; lowest price first
            sell_orders = cls.objects.filter(
                stock=stock,
                action='Sell',
                status__in=['Pending', 'Partially Completed']
            ).order_by('price', 'created_at')  # Lowest price first
        else:
            # Limit Buy: price__lte=buy_order.price
            sell_orders = cls.objects.filter(
                stock=stock,
                action='Sell',
                status__in=['Pending', 'Partially Completed'],
                price__lte=buy_order.price
            ).order_by('price', 'created_at')  # Lowest price first

        for pending_sell in sell_orders:
            if buy_order.quantity == 0:
                break

            # The trade price is the seller's price (in a simple matching engine)
            trade_price = pending_sell.price
            trade_quantity = min(buy_order.quantity, pending_sell.quantity)

            trade_buyer, trade_seller = Trade.execute_trade(buy_order, pending_sell, trade_quantity, trade_price)

            # Update quantities
            buy_order.quantity -= trade_quantity
            pending_sell.quantity -= trade_quantity

            # Update statuses
            if pending_sell.quantity == 0:
                pending_sell.status = 'Fully Completed'
            else:
                pending_sell.status = 'Partially Completed'
            pending_sell.save()

            if buy_order.quantity == 0:
                buy_order.status = 'Fully Completed'
            else:
                buy_order.status = 'Partially Completed'
            buy_order.save()

        # 2. If there's remaining quantity, buy from the company (only if Market or if stock.current_price <= limit)
        if buy_order.quantity > 0:
            if buy_order.order_type == 'Market':
                available_shares = stock.available_shares
                if available_shares > 0:
                    trade_quantity = min(buy_order.quantity, available_shares)
                    trade_price = stock.current_price
                    trade_buyer, trade_seller = Trade.execute_trade(buy_order, None, trade_quantity, trade_price)

                    stock.available_shares -= trade_quantity
                    stock.save()

                    buy_order.quantity -= trade_quantity
                    if buy_order.quantity == 0:
                        buy_order.status = 'Fully Completed'
                    else:
                        buy_order.status = 'Partially Completed'
                    buy_order.save()

            elif buy_order.order_type == 'Limit':
                # Buy from the company if company's price <= buy_order.price
                if stock.current_price <= buy_order.price:
                    available_shares = stock.available_shares
                    if available_shares > 0:
                        trade_quantity = min(buy_order.quantity, available_shares)
                        trade_price = stock.current_price
                        trade_buyer, trade_seller = Trade.execute_trade(buy_order, None, trade_quantity, trade_price)

                        stock.available_shares -= trade_quantity
                        stock.save()

                        buy_order.quantity -= trade_quantity
                        if buy_order.quantity == 0:
                            buy_order.status = 'Fully Completed'
                        else:
                            buy_order.status = 'Partially Completed'
                        buy_order.save()

    @classmethod
    def _handle_sell_order(cls, sell_order):
        """Process Market/Limit Sell: match with highest-price Buy orders; partial fill leftover remains pending."""
        stock = sell_order.stock

        # -- STATUS CORRECTION: we look for buy orders with status in ['Pending', 'Partially Completed'].
        if sell_order.order_type == 'Market':
            # Match with Buy orders at highest price first
            buy_orders = cls.objects.filter(
                stock=stock,
                action='Buy',
                status__in=['Pending', 'Partially Completed']
            ).order_by('-price', 'created_at')  # Highest price first
        else:  # Limit
            # Limit Sell: price__gte=sell_order.price
            buy_orders = cls.objects.filter(
                stock=stock,
                action='Buy',
                status__in=['Pending', 'Partially Completed'],
                price__gte=sell_order.price
            ).order_by('-price', 'created_at')  # Highest price first

        for pending_buy in buy_orders:
            if sell_order.quantity == 0:
                break

            # The trade price can be the buyer's price (common approach).
            trade_price = pending_buy.price if pending_buy.order_type == 'Limit' else stock.current_price
            trade_quantity = min(sell_order.quantity, pending_buy.quantity)

            trade_buyer, trade_seller = Trade.execute_trade(pending_buy, sell_order, trade_quantity, trade_price)

            # Update quantities
            sell_order.quantity -= trade_quantity
            pending_buy.quantity -= trade_quantity

            # Update statuses
            if pending_buy.quantity == 0:
                pending_buy.status = 'Fully Completed'
            else:
                pending_buy.status = 'Partially Completed'
            pending_buy.save()

            if sell_order.quantity == 0:
                sell_order.status = 'Fully Completed'
            else:
                sell_order.status = 'Partially Completed'
            sell_order.save()


class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='trades')
    order = models.ForeignKey(
        'Orders',
        on_delete=models.CASCADE,
        related_name='trades',
        null=True,
        blank=True
    )
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    trade_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Trade by {self.user.username} on {self.trade_time.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def execute_trade(cls, buy_order, sell_order, quantity, price=None):
        """
        Executes a trade between a buy order and a sell order (or company, if sell_order=None).
        Updates buyer/seller account balance & portfolio, logs the transaction, and sends notifications.
        """
        if price is None:
            if sell_order:
                price = sell_order.stock.current_price
            else:
                price = buy_order.stock.current_price

        TRANSACTION_FEE_PERCENTAGE = Decimal('0.01')  # 1%
        total_cost = Decimal(quantity) * Decimal(price)
        transaction_fee_buyer = (total_cost * TRANSACTION_FEE_PERCENTAGE).quantize(Decimal('0.01'))

        with transaction.atomic():
            # Buyer side
            trade_buyer = cls.objects.create(
                user=buy_order.user,
                stock=buy_order.stock,
                order=buy_order,
                quantity=quantity,
                price=price,
                transaction_fee=transaction_fee_buyer
            )
            buy_order.user.account_balance -= (total_cost + transaction_fee_buyer)
            buy_order.user.save()

            buy_order.transaction_fee += transaction_fee_buyer
            buy_order.save()

            # Identify seller details
            if sell_order:
                seller_user = sell_order.user
                seller_username = seller_user.username
            else:
                seller_user = None
                seller_username = buy_order.stock.company.company_name

            # Buyer Audit Trail
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
                # Seller side
                transaction_fee_seller = (total_cost * TRANSACTION_FEE_PERCENTAGE).quantize(Decimal('0.01'))
                trade_seller = cls.objects.create(
                    user=sell_order.user,
                    stock=sell_order.stock,
                    order=sell_order,
                    quantity=quantity,
                    price=price,
                    transaction_fee=transaction_fee_seller
                )
                sell_order.user.account_balance += (total_cost - transaction_fee_seller)
                sell_order.user.save()

                sell_order.transaction_fee += transaction_fee_seller
                sell_order.save()

                # Seller Audit Trail
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

                # Update Seller's Portfolio
                cls._update_portfolio(
                    user=sell_order.user,
                    stock=sell_order.stock,
                    quantity=quantity,
                    price=price,
                    is_buy=False
                )

                # SuspiciousActivity checks
                detect_suspicious_trade(trade_buyer)
                detect_suspicious_trade(trade_seller)

                # Notifications to both buyer & seller
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
                # Direct purchase from company => only notify buyer
                send_order_notification(
                    to_email=buy_order.user.email,
                    username=buy_order.user.username,
                    action="Buy",
                    stock_symbol=buy_order.stock.ticker_symbol,
                    quantity=quantity,
                    price=price,
                    new_balance=buy_order.user.account_balance
                )

            # Update Buyer's Portfolio
            cls._update_portfolio(
                user=buy_order.user,
                stock=buy_order.stock,
                quantity=quantity,
                price=price,
                is_buy=True
            )

            # After completing the trade execution, invoke suspicious trade detection
            detect_suspicious_trade(trade_buyer)
            if trade_seller:
                detect_suspicious_trade(trade_seller)

            return trade_buyer, trade_seller

    @staticmethod
    def _update_portfolio(user, stock, quantity, price, is_buy):
        """
        Updates the user's portfolio upon trade execution.
        """
        quantity = int(quantity)  # Ensure quantity is integer
        price = Decimal(price)

        with transaction.atomic():
            portfolio, created = UsersPortfolio.objects.select_for_update().get_or_create(user=user)
            if is_buy:
                portfolio.quantity += quantity
                portfolio.total_investment += quantity * price
                if portfolio.quantity > 0:
                    portfolio.average_purchase_price = (portfolio.total_investment / portfolio.quantity).quantize(Decimal('0.01'))
            else:
                portfolio.quantity -= quantity
                # We subtract from total_investment based on the average purchase price,
                # not the current trade price, to keep consistent cost basis.
                portfolio.total_investment -= quantity * portfolio.average_purchase_price
                if portfolio.quantity > 0:
                    portfolio.average_purchase_price = (portfolio.total_investment / portfolio.quantity).quantize(Decimal('0.01'))
                else:
                    portfolio.average_purchase_price = Decimal('0.00')
            portfolio.save()


def notify_user_real_time(user, message):
    """
    Real-time notification using Django Channels (optional).
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": {"content": message},
        }
    )


# Additional models for Dividend, DailyClosingPrice, Disclosure, etc.

class Dividend(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='dividends')
    budget_year = models.CharField(max_length=4)
    dividend_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    total_dividend_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=15,
        choices=[('Paid', 'Paid'), ('Pending', 'Pending'), ('Disbursed', 'Disbursed')],
        default='Pending'
    )

    class Meta:
        unique_together = ('company', 'budget_year')

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
    type = models.CharField(
        max_length=50,
        choices=DisclosureTypes.choices,
        help_text=_("Type of disclosure, e.g. 'Financial Statement', 'Annual Report'.")
    )
    year = models.PositiveIntegerField(help_text=_("Fiscal/reporting year for this disclosure."))
    file = models.FileField(upload_to='disclosures/', help_text=_("File containing disclosure document."))
    description = models.TextField(null=True, blank=True, help_text=_("Optional description or summary."))
    uploaded_at = models.DateTimeField(auto_now_add=True, help_text=_("Timestamp of upload."))

    class Meta:
        ordering = ['-year', '-uploaded_at']
        verbose_name = "Disclosure"
        verbose_name_plural = "Disclosures"

    def __str__(self):
        return f"{self.get_type_display()} ({self.year}) - {self.company.company_name}"


class DividendDistribution(models.Model):
    """
    Stores the dividend disbursed to each user for a particular Dividend record.
    """
    dividend = models.ForeignKey(
        'Dividend',
        on_delete=models.CASCADE,
        related_name='distributions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dividend_distributions'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"DividendDistribution: Dividend={self.dividend.id}, "
                f"User={self.user.username}, Amount={self.amount}")


class DividendDetailedHolding(models.Model):
    dividend = models.ForeignKey(
        'Dividend',
        on_delete=models.CASCADE,
        related_name='detailed_holdings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dividend_holdings'
    )
    username = models.CharField(max_length=50)
    stock_symbol = models.CharField(max_length=10)
    order_type = models.CharField(max_length=20, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.IntegerField()
    transaction_fee = models.DecimalField(max_digits=15, decimal_places=2)
    total_buying_price = models.DecimalField(max_digits=15, decimal_places=2)
    weighted_value = models.DecimalField(max_digits=15, decimal_places=2)
    dividend_eligible = models.CharField(max_length=5)
    trade_time = models.DateTimeField()

    ratio_at_creation = models.DecimalField(max_digits=15, decimal_places=8, default=Decimal('0.00000000'))
    paid_dividend = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    # NEW FIELDS
    company_id = models.IntegerField(null=True, blank=True)
    budget_year = models.CharField(max_length=4, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Div={self.dividend_id}] {self.user.username} - {self.stock_symbol} - ratio={self.ratio_at_creation}"
