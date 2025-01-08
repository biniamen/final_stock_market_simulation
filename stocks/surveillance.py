# stocks/surveillance.py

import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum

from .models import Trade  # Move imports to top unless you're certain you have a circular import
from .models_suspicious import SuspiciousActivity

logger = logging.getLogger(__name__)

def detect_suspicious_trade(trade):
    """
    Enhanced suspicious trade detection logic. This function checks multiple
    criteria and logs each reason if suspicious. If any suspicious criteria are
    met, a SuspiciousActivity record is created.
    """
    reasons = []

    # --- 1) Unusual Trade Volume ---------------------------------------------
    # Example: If the trade quantity is more than 10% of the total market float 
    # (company's current available_shares + total traded so far), mark suspicious.
    stock = trade.stock
    total_traded = Trade.objects.filter(stock=stock).aggregate(Sum('quantity'))['quantity__sum'] or 0
    market_float = stock.available_shares + total_traded

    if market_float > 0:  
        unusual_volume_threshold = 0.1 * market_float  # 10%
        if trade.quantity > unusual_volume_threshold:
            reasons.append(
                f"Unusually high volume: {trade.quantity} exceeds 10% of market float ({unusual_volume_threshold:.0f})."
            )

    # --- 2) Price Manipulation -----------------------------------------------
    # Example: If the trade price deviates ±20% from the stock's average trade price, mark suspicious.
    avg_price = Trade.objects.filter(stock=stock).aggregate(Avg('price'))['price__avg']
    if avg_price and avg_price > 0:
        upper_limit = 1.2 * avg_price
        lower_limit = 0.8 * avg_price
        if not (lower_limit <= trade.price <= upper_limit):
            reasons.append(
                f"Potential price manipulation: Trade price {trade.price} deviates >20% from avg {avg_price:.2f}."
            )

    # --- 3) Frequent Trader Activity -----------------------------------------
    # Example: If the user has made more than 5 trades in the last 10 minutes, mark suspicious.
    time_threshold = timezone.now() - timedelta(minutes=10)
    recent_trades_count = Trade.objects.filter(
        user=trade.user,
        trade_time__gte=time_threshold
    ).count()

    # Adjust the threshold to match your business logic
    if recent_trades_count > 1:
        reasons.append(
            f"High trading frequency: {recent_trades_count} trades in the last 10 minutes."
        )

    # --- 4) Create SuspiciousActivity if needed ------------------------------
    if reasons:
        # Combine all reasons in a single record
        suspicious_record = SuspiciousActivity.objects.create(
            trade=trade,
            reason="; ".join(reasons),
        )
        logger.warning(
            f"SuspiciousActivity #{suspicious_record.id} created for Trade #{trade.id} "
            f"by {trade.user.username}. Reasons: {reasons}"
        )
        # Optionally, you could send an email, Slack message, or real-time
        # notification to compliance officers or admin staff here.
    else:
        logger.debug(f"Trade #{trade.id} for user '{trade.user.username}' is NOT suspicious.")
