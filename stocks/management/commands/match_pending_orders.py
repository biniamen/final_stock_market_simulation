# stocks/management/commands/match_pending_orders.py

import sys
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from stocks.models import Orders

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = """
    Scans all pending orders in the database and attempts to match them
    using the existing Orders.match_and_execute_orders() logic.
    
    Usage: 
        python manage.py match_pending_orders
    """

    def handle(self, *args, **options):
        try:
            self.stdout.write("Starting matching process for pending orders...")

            # Step 1: Fetch all pending orders. 
            #   Typically you might fetch in chronological order, or by best price, 
            #   but let's keep it simple and just order by created_at.
            pending_orders = Orders.objects.filter(status='Pending').order_by('created_at')

            if not pending_orders.exists():
                self.stdout.write("No pending orders found.")
                return

            # Step 2: Loop and match
            for order in pending_orders:
                with transaction.atomic():
                    # Re-fetch the order to ensure it’s still pending
                    order.refresh_from_db()
                    if order.status != 'Pending':
                        continue  # skip if it's no longer pending

                    # Call the existing method from your Orders model
                    Orders.match_and_execute_orders(order)
                    # The above code will attempt to match the order 
                    # with suitable Buy/Sell orders. 

                    # You could add logging for each order
                    logger.info(f"Processed matching for Order ID={order.id}. Status is now {order.status}")

            self.stdout.write("Matching process completed successfully.")

        except Exception as e:
            logger.error(f"Error while matching pending orders: {str(e)}", exc_info=True)
            self.stderr.write(f"Error: {str(e)}")
            sys.exit(1)
