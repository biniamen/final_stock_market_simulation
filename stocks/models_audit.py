# models_audit.py or models.py (wherever you keep your models)
from django.db import models
from django.utils import timezone
from decimal import Decimal

from django.db import models

class TransactionAuditTrail(models.Model):
    EVENT_TYPE_CHOICES = [
        ('OrderCreated', 'Order Created'),
        ('TradeExecuted', 'Trade Executed'),
        ('TransactionFeeDeducted', 'Transaction Fee Deducted'),
        ('Direct Purchase', 'Direct Purchase'),
        # Add other event types as needed
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    order = models.ForeignKey('Orders', on_delete=models.CASCADE, null=True, blank=True)
    trade = models.ForeignKey('Trade', on_delete=models.CASCADE, null=True, blank=True)
    details = models.JSONField()  # Use JSONField for structured details
    timestamp = models.DateTimeField(auto_now_add=True, null=True)  # Initially nullable

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"
