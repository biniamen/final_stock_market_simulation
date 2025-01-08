from django.db import models

class SuspiciousActivity(models.Model):
    trade = models.ForeignKey('stocks.Trade', on_delete=models.CASCADE, related_name='suspicious_activities')
    reason = models.TextField()
    flagged_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Suspicious Trade: {self.trade.id} - {self.reason[:50]}"
