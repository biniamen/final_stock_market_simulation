# regulations/management/commands/cancel_pending_orders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from stocks.models import Orders
from regulations.models import WorkingHours
from decimal import Decimal

class Command(BaseCommand):
    help = 'Cancels pending orders after working hours.'

    def handle(self, *args, **kwargs):
        current_time = timezone.localtime()
        current_day = current_time.strftime('%A')

        self.stdout.write(f"Executing cancel_pending_orders at {current_time} on {current_day}")

        # Retrieve today's working hours
        try:
            working_hours = WorkingHours.objects.get(day_of_week=current_day)
        except WorkingHours.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No working hours defined for {current_day}. Exiting."))
            return

        end_time = working_hours.end_time

        # Check if current time is past end_time
        if current_time.time() > end_time:
            pending_orders = Orders.objects.filter(status='Pending')
            updated_count = pending_orders.update(status='Cancelled')
            self.stdout.write(self.style.SUCCESS(f"Cancelled {updated_count} pending orders."))
        else:
            self.stdout.write(self.style.WARNING("Current time is before the end of working hours. No action taken."))
