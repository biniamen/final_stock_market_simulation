# stocks/management/commands/cancel_pending_orders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from stocks.models import Orders, TransactionAuditTrail

class Command(BaseCommand):
    help = 'Cancels all pending orders at the end of the trading day.'

    def handle(self, *args, **options):
        current_time = timezone.now()
        # Define end of trading day time, e.g., 5 PM
        end_of_day_time = current_time.replace(hour=17, minute=0, second=0, microsecond=0)

        if current_time >= end_of_day_time:
            pending_orders = Orders.objects.filter(status='Pending')
            for order in pending_orders:
                order.status = 'Cancelled'
                order.save()
                # Log audit trail for cancellation
                TransactionAuditTrail.objects.create(
                    event_type='OrderStatusChanged',
                    order=order,
                    details=(
                        f"Order automatically cancelled at end of day. "
                        f"Action: {order.action}, Type: {order.order_type}, Quantity: {order.quantity}, Price: {order.price}"
                    )
                )
            self.stdout.write(self.style.SUCCESS('Successfully cancelled all pending orders.'))
        else:
            self.stdout.write(self.style.WARNING('It is not the end of the trading day yet.'))
