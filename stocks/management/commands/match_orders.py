from django.core.management.base import BaseCommand
from stocks.models import Orders

class Command(BaseCommand):
    help = 'Match and execute pending orders using the Price-Time Priority Algorithm'

    def handle(self, *args, **kwargs):
        Orders.match_and_execute_orders()
        self.stdout.write(self.style.SUCCESS('Successfully matched and executed pending orders.'))
