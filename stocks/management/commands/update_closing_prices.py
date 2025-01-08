from django.core.management.base import BaseCommand
from django.db.models import Max
from stocks.models import Trade, Stocks, DailyClosingPrice
from datetime import date

class Command(BaseCommand):
    help = 'Update daily closing prices from trades at end of working hours.'

    def handle(self, *args, **options):
        # Get max price per stock from trades of the current day
        today = date.today()
        closing_prices = Trade.objects.filter(trade_time__date=today).values('stock').annotate(max_price=Max('price'))
        
        for cp in closing_prices:
            stock_id = cp['stock']
            max_price = cp['max_price']
            stock = Stocks.objects.get(id=stock_id)

            DailyClosingPrice.objects.create(
                stock=stock,
                date=today,
                closing_price=max_price
            )

        self.stdout.write(self.style.SUCCESS('Daily closing prices updated successfully!'))
