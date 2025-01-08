from django.core.management.base import BaseCommand
from stock.models import Orders
from regulations.utils import get_regulation_value
from django.utils.timezone import now

class Command(BaseCommand):
    help = "Cancel pending orders outside working hours"

    def handle(self, *args, **kwargs):
        working_hours = get_regulation_value("Working Hours")
        if working_hours:
            start, end = map(int, working_hours.split('-'))
            current_hour = now().hour
            if not (start <= current_hour < end):
                Orders.objects.filter(status="Pending").update(status="Cancelled")
                self.stdout.write("Pending orders have been canceled.")
            else:
                self.stdout.write("No orders canceled, within working hours.")
