# stocks/surveillance_utils.py

import logging
from django.apps import apps
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum

logger = logging.getLogger(__name__)

def detect_suspicious_trade(trade):
    """
    Enhanced suspicious-trade detection logic. Checks multiple criteria
    and logs each reason if suspicious. If any suspicious criteria are
    met, a SuspiciousActivity record is created.
    """

    # 1. Safely get the Trade and SuspiciousActivity models
    Trade = apps.get_model('stocks', 'Trade')
    SuspiciousActivity = apps.get_model('stocks', 'SuspiciousActivity')

    reasons = []

    # --- 1) Unusual Trade Volume ---
    stock = trade.stock
    total_traded = Trade.objects.filter(stock=stock).aggregate(Sum('quantity'))['quantity__sum'] or 0
    market_float = stock.available_shares + total_traded

    if market_float > 0:
        # E.g., 10% threshold
        unusual_volume_threshold = 0.1 * market_float
        if trade.quantity > unusual_volume_threshold:
            reasons.append(
                f"Unusually high volume: {trade.quantity} exceeds 10% "
                f"of market float ({unusual_volume_threshold:.0f})."
            )

    # --- 2) Price Manipulation ---
    avg_price = Trade.objects.filter(stock=stock).aggregate(Avg('price'))['price__avg']
    if avg_price and avg_price > 0:
        upper_limit = 1.2 * avg_price
        lower_limit = 0.8 * avg_price
        if not (lower_limit <= trade.price <= upper_limit):
            reasons.append(
                f"Potential price manipulation: Trade price {trade.price} "
                f"deviates >20% from avg {avg_price:.2f}."
            )

    # --- 3) Frequent Trader Activity ---
    time_threshold = timezone.now() - timedelta(minutes=10)
    recent_trades_count = Trade.objects.filter(
        user=trade.user, 
        trade_time__gte=time_threshold
    ).count()

    # E.g., more than 5 trades in 10 mins
    if recent_trades_count > 5:
        reasons.append(
            f"High trading frequency: {recent_trades_count} trades in "
            f"the last 10 minutes."
        )

    # --- 4) Create SuspiciousActivity if needed ---
    if reasons:
        # Combine all reasons in a single record
        suspicious_record = SuspiciousActivity.objects.create(
            trade=trade,
            reason="; ".join(reasons)
        )
        logger.warning(
            f"SuspiciousActivity #{suspicious_record.id} created for "
            f"Trade #{trade.id} by {trade.user.username}. Reasons: {reasons}"
        )
    else:
        logger.debug(
            f"Trade #{trade.id} for user '{trade.user.username}' is NOT suspicious."
        )
