# stocks/surveillance_utils.py

import logging
from decimal import Decimal
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum, Count

logger = logging.getLogger(__name__)

def detect_suspicious_trade(trade):
    """
    Flags a trade as suspicious based on defined criteria without blocking the transaction.
    """
    logger.debug(f"Starting suspicious trade detection for Trade ID: {trade.id}")

    # Load thresholds from settings or define default values
    thresholds = getattr(settings, 'SUSPICIOUS_TRADE_THRESHOLDS', {})
    volume_ratio = thresholds.get('unusual_volume_ratio', 0.1)           # 10%
    price_deviation = thresholds.get('price_deviation', 0.2)            # ±20%
    freq_threshold = thresholds.get('trade_frequency_threshold', 2)      # More than 1 trade (i.e., 2 or more)
    freq_minutes = thresholds.get('trade_frequency_minutes', 10)         # within 10 minutes

    logger.debug(f"Thresholds - Volume Ratio: {volume_ratio}, Price Deviation: {price_deviation}, "
                 f"Frequency Threshold: {freq_threshold}, Frequency Minutes: {freq_minutes}")

    # Get models
    TradeModel = apps.get_model('stocks', 'Trade')
    SuspiciousActivityModel = apps.get_model('stocks', 'SuspiciousActivity')

    reasons = []

    # --- 1) Unusual Trade Volume ---
    stock = trade.stock
    total_traded = TradeModel.objects.filter(stock=stock).aggregate(Sum('quantity'))['quantity__sum'] or 0
    market_float = stock.available_shares + total_traded
    logger.debug(f"Stock: {stock.ticker_symbol}, Total Traded: {total_traded}, Market Float: {market_float}")

    if market_float > 0:
        threshold_volume = volume_ratio * market_float
        logger.debug(f"Threshold Volume: {threshold_volume}, Trade Quantity: {trade.quantity}")
        if trade.quantity > threshold_volume:
            reasons.append(
                f"Unusually high volume: {trade.quantity} exceeds {volume_ratio*100:.0f}% "
                f"of market float ({threshold_volume:.0f})."
            )
            logger.debug("Unusual volume condition met.")

    # --- 2) Price Manipulation ---
    avg_price = TradeModel.objects.filter(stock=stock).aggregate(Avg('price'))['price__avg']
    logger.debug(f"Average Price for {stock.ticker_symbol}: {avg_price}")
    if avg_price and avg_price > 0:
        upper_limit = (Decimal('1') + Decimal(price_deviation)) * Decimal(avg_price)
        lower_limit = (Decimal('1') - Decimal(price_deviation)) * Decimal(avg_price)
        logger.debug(f"Price Limits - Lower: {lower_limit}, Upper: {upper_limit}, Trade Price: {trade.price}")
        if not (lower_limit <= trade.price <= upper_limit):
            reasons.append(
                f"Potential price manipulation: Trade price {trade.price} deviates > "
                f"{price_deviation*100:.0f}% from avg {avg_price:.2f}."
            )
            logger.debug("Price manipulation condition met.")

    # --- 3) Frequent Trader Activity ---
    time_threshold = timezone.now() - timedelta(minutes=freq_minutes)
    recent_trades_count = TradeModel.objects.filter(
        user=trade.user,
        stock=stock,
        trade_time__gte=time_threshold
    ).count()
    logger.debug(f"Recent Trades Count: {recent_trades_count} within last {freq_minutes} minutes.")

    if recent_trades_count >= freq_threshold:
        reasons.append(
            f"High trading frequency: {recent_trades_count} trades of {stock.ticker_symbol} "
            f"in the last {freq_minutes} minutes."
        )
        logger.debug("Frequent trading activity condition met.")

    # --- 4) Create SuspiciousActivity if needed ---
    if reasons:
        try:
            suspicious_record = SuspiciousActivityModel.objects.create(
                trade=trade,
                reason="; ".join(reasons)
            )
            logger.warning(
                f"SuspiciousActivity #{suspicious_record.id} created for "
                f"Trade #{trade.id} by user '{trade.user.username}'. Reasons: {reasons}"
            )
        except Exception as e:
            logger.error(f"Failed to create SuspiciousActivity for Trade #{trade.id}: {e}")
    else:
        logger.debug(f"Trade #{trade.id} for user '{trade.user.username}' is NOT suspicious.")
