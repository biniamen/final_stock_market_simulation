from celery import shared_task
from django.utils.timezone import localtime
from stocks.models import Orders
from regulations.models import WorkingHours


@shared_task
def cancel_pending_orders():
    """
    Cancels pending orders after the working hours for the current day.
    """
    current_time = localtime()
    current_day = current_time.strftime('%A')

    # Check for today's working hours
    try:
        working_hours = WorkingHours.objects.get(day_of_week=current_day)
    except WorkingHours.DoesNotExist:
        # If working hours are not configured, return
        return

    # If the current time is after end_time, cancel pending orders
    if current_time.time() > working_hours.end_time:
        pending_orders = Orders.objects.filter(status='Pending')
        pending_orders.update(status='Cancelled')
