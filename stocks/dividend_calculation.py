import datetime
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import DividendDistribution, Dividend, Trade, UsersPortfolio
from django.contrib.auth import get_user_model

User = get_user_model()

def _get_fiscal_year_dates(budget_year):
    """
    Given a budget_year string like '2023/24', return start_date and end_date:
    - start_date = July 1 of the first year (2023-07-01)
    - end_date   = June 30 of the second year (2024-06-30)
    """
    # Typically budget_year might be '2023/24'
    # We'll split at '/' to parse year1, year2
    parts = budget_year.split('/')
    if len(parts) != 2:
        raise ValueError("budget_year must be in the format 'YYYY/YY' (e.g. '2023/24')")

    start_year_str, _ = parts
    start_year = int(start_year_str)
    # For the example '2023/24', the start is 2023-07-01, end is 2024-06-30
    start_date = datetime.date(start_year, 7, 1)
    end_date = datetime.date(start_year + 1, 6, 30)
    return start_date, end_date

def _days_held_within_range(buy_date, sell_date, start_date, end_date):
    """
    Returns the number of days a user holds a stock within the [start_date, end_date] window.
    - buy_date, sell_date are dates of purchase and sale
    - If sell_date is None, we assume still holding up to end_date.
    """
    # The holding period is from max(buy_date, start_date) to min(sell_date or end_date, end_date)
    if sell_date is None:
        sell_date = end_date  # hold until end_date if not sold

    holding_start = max(buy_date, start_date)
    holding_end = min(sell_date, end_date)
    delta = (holding_end - holding_start).days
    return max(delta, 0)  # if negative, return 0

def _compute_user_weighted_stock_value(user, company, start_date, end_date):
    """
    Compute the total "weighted stock value" for the user for the given company
    within the [start_date, end_date] window.

    Weighted formula:
        WeightedValue = (DaysHeld / 365) * (Quantity * current_price)
    
    Because quantity or price can change over time, you need a business approach:
    1. If your system always uses 'stock.current_price' as the final price, 
       then the user is referencing the final price or an average price. 
       For simplicity, let's use the company's stock's current_price. 
       (Alternatively, you might have a closing price each day, or some average approach.)

    2. For the quantity, you need to find the net shares the user actually holds 
       within that period. 
    """
    # 1) For simplicity, assume each company has exactly ONE main stock:
    #    Or you define a rule to pick a particular stock from the company.
    stock_qs = company.stocks.all()
    if not stock_qs.exists():
        return Decimal('0.00')
    stock = stock_qs.first()  # if multiple stocks exist, you need a clearer approach

    current_price = stock.current_price or Decimal('0.00')

    # A robust approach would track each partial buy/sell inside the date range.
    # For demonstration, let's do something simpler:
    # We'll look at all trades (both buy & sell) the user made for that stock
    # and compute day segments. We assume each Trade has:
    #   - trade_time (datetime)
    #   - quantity (positive if buy, negative if sell) => In your code, buy and sell trades 
    #        are separate records. We might need to track them differently.

    # However, in your current code, each trade is strictly a buy or sell with a positive quantity 
    # and we rely on the order.action to differentiate. We can re-construct holdings per period.

    # To keep an example approach: 
    #  - We'll gather all BUY trades that occurred before end_date 
    #  - We'll gather SELL trades that occurred before end_date
    #  - We'll build intervals. (This is non-trivial in a real system.)
    #
    # A simpler approach: If your system doesn't track partial changes daily, 
    # you might just check if the user still holds shares. Then you measure the difference 
    # between the purchase date and end_date. 
    # The example in your question suggests the user holds a consistent quantity from buy date 
    # to the end of the period. If they sold earlier, maybe 0 days beyond that sale date.

    # In the snippet below, we do a naive approach: 
    # For each buy trade in the range, see if there's a corresponding sell that offsets it, etc.

    # WARNING: This is simplified and might not handle multiple partial buys/sells in the same year. 
    # Adjust as needed.

    # Let's fetch all trades for the user & stock, ordered by time
    all_trades = (
        user.trades
            .filter(stock=stock)
            .order_by('trade_time')
    )

    total_weighted_value = Decimal('0.00')
    # We'll keep track of an ongoing "open lot" approach.
    # Each "buy" creates a lot (with date, quantity).
    # Each "sell" reduces from the earliest open lot. 
    # Then we figure out how many days that lot was held in [start_date, end_date].

    open_lots = []  # list of dicts: [{"quantity": x, "buy_date": date}, ...]

    for trade in all_trades:
        trade_date = trade.trade_time.date()
        if trade.order.action == 'Buy':
            # Add a new lot
            open_lots.append({
                "quantity": trade.quantity,
                "buy_date": trade_date
            })
        elif trade.order.action == 'Sell':
            # Subtract from the earliest open lot(s)
            qty_to_close = trade.quantity
            while qty_to_close > 0 and len(open_lots) > 0:
                lot = open_lots[0]
                if lot["quantity"] <= qty_to_close:
                    # Entire lot is closed (sold)
                    days_held = _days_held_within_range(
                        lot["buy_date"],
                        trade_date,  # sold on this date
                        start_date,
                        end_date
                    )
                    # Weighted for that closed lot
                    # (days_held / 365) * (lot_quantity * current_price)
                    lot_value = (Decimal(days_held) / Decimal('365')) * \
                                (Decimal(lot["quantity"]) * current_price)
                    total_weighted_value += lot_value

                    qty_to_close -= lot["quantity"]
                    open_lots.pop(0)  # remove this lot
                else:
                    # This sell partially closes the lot
                    lot["quantity"] -= qty_to_close
                    days_held = _days_held_within_range(
                        lot["buy_date"],
                        trade_date,
                        start_date,
                        end_date
                    )
                    partial_value = (Decimal(days_held) / Decimal('365')) * \
                                    (Decimal(qty_to_close) * current_price)
                    total_weighted_value += partial_value
                    qty_to_close = 0

    # Now, after processing all trades up to end_date, 
    # some lots might remain "open" (not sold). 
    # We treat them as being held until end_date
    for lot in open_lots:
        days_held = _days_held_within_range(
            lot["buy_date"],
            None,  # meaning up to end_date
            start_date,
            end_date
        )
        lot_value = (Decimal(days_held) / Decimal('365')) * \
                    (Decimal(lot["quantity"]) * current_price)
        total_weighted_value += lot_value

    return total_weighted_value


@transaction.atomic
def distribute_dividend(dividend_id, executed_by=None):
    """
    Core logic to:
      1) Find the dividend record
      2) Determine the fiscal year date range (July 1 -> June 30)
      3) Calculate sum of all WeightedStockValues across all users
      4) dividend_ratio = total_dividend_amount / sum_of_all_weighted_values
      5) For each user who has WeightedStockValue > 0, pay them: 
         user_dividend = user_weighted_value * dividend_ratio
      6) Create DividendDistribution records for each payout
      7) Mark Dividend as 'Paid'

    Raises an exception if sum_of_all_weighted_values is 0.
    """
    dividend = Dividend.objects.select_for_update().get(id=dividend_id)
    if dividend.status == 'Paid':
        raise ValueError("This dividend has already been paid.")

    start_date, end_date = _get_fiscal_year_dates(dividend.budget_year)

    # Gather all possible *traders*. For example, let's get all users who have 
    # at least one trade in that date range for the same company's stock(s).
    company = dividend.company
    # We'll do a naive approach: gather all trades for the company's stock(s) during or before end_date
    # and get unique user IDs.
    stock_ids = company.stocks.values_list('id', flat=True)
    trader_ids = (
        Trade.objects
             .filter(stock_id__in=stock_ids)
             .values_list('user_id', flat=True)
             .distinct()
    )

    total_weighted_sum = Decimal('0.00')
    user_weighted_values = {}

    for user_id in trader_ids:
        user = User.objects.get(id=user_id)
        user_value = _compute_user_weighted_stock_value(user, company, start_date, end_date)
        if user_value > 0:
            user_weighted_values[user_id] = user_value
            total_weighted_sum += user_value

    if total_weighted_sum <= 0:
        # If no one actually held the stock in that range
        raise ValueError("No valid holdings found in this fiscal year range, or total is 0. Cannot distribute.")

    # Compute ratio
    # e.g. ratio = 1_000_000 / 1_800_000 = ~0.5555
    ratio = dividend.total_dividend_amount / total_weighted_sum

    # Create DividendDistribution records & credit users
    distributions = []
    for user_id, weighted_val in user_weighted_values.items():
        user_dividend = (weighted_val * ratio).quantize(Decimal('0.00'))
        if user_dividend > 0:
            # Save the distribution
            dist = DividendDistribution(
                dividend=dividend,
                user_id=user_id,
                amount=user_dividend
            )
            distributions.append(dist)
    DividendDistribution.objects.bulk_create(distributions)

    # Optionally, update the dividend_ratio field for future reference
    # (This is an optional step: you might store a ratio in the Dividend model)
    dividend.dividend_ratio = ratio.quantize(Decimal('0.00'))
    dividend.status = 'Paid'
    dividend.save()

    # You might also want to log who triggered the distribution (executed_by), 
    # or send out notifications, etc.
    return distributions
