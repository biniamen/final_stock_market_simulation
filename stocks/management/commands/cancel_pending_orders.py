# stocks/management/commands/cancel_pending_orders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from regulations.models import WorkingHours  # Import from the correct app
from stocks.models import Orders, TransactionAuditTrail  # Adjust import as necessary

class Command(BaseCommand):
    help = 'Cancels all pending orders at the end of the trading day.'

    def handle(self, *args, **options):
        # Get the current datetime with timezone awareness
        current_time = timezone.now()
        current_day_of_week = current_time.strftime('%A')  # e.g., 'Monday', 'Tuesday', etc.

        try:
            # Retrieve the working hours for the current day of the week
            working_hours = WorkingHours.objects.get(day_of_week=current_day_of_week)
            end_time = working_hours.end_time  # This should be a TimeField
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(f'Working hours for {current_day_of_week} are not defined.'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while fetching working hours: {e}'))
            return

        # Combine current date with end_time to get a complete datetime
        naive_end_of_day_datetime = timezone.datetime.combine(current_time.date(), end_time)
        end_of_day_datetime = timezone.make_aware(
            naive_end_of_day_datetime,
            timezone.get_current_timezone()
        )

        if current_time >= end_of_day_datetime:
            pending_orders = Orders.objects.filter(status='Pending')
            if pending_orders.exists():
                for order in pending_orders:
                    order.status = 'Cancelled'
                    order.save()

                    # Log audit trail for cancellation
                    TransactionAuditTrail.objects.create(
                        event_type='OrderStatusChanged',
                        order=order,
                        details=(
                            f"Order automatically cancelled at end of day. "
                            f"Action: {order.action}, Type: {order.order_type}, "
                            f"Quantity: {order.quantity}, Price: {order.price}"
                        )
                    )
                self.stdout.write(self.style.SUCCESS('Successfully cancelled all pending orders.'))
            else:
                self.stdout.write(self.style.WARNING('No pending orders to cancel.'))
        else:
            time_remaining = end_of_day_datetime - current_time
            hours, remainder = divmod(time_remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            self.stdout.write(
                self.style.WARNING(
                    f'It is not the end of the trading day yet. '
                    f'Time remaining: {hours}h {minutes}m.'
                )
            )
