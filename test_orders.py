from stocks.models import Orders

def run_test_cases(stock, user1, user2):
    print("Running test cases...")

    # Test Case 1: Market Buy Order
    print("\nTest Case 1: Market Buy Order")
    Orders.objects.create(
        user=user2,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Sell",
        price=105.00,  # Higher price
        quantity=50,
        status="Pending"
    )
    Orders.objects.create(
        user=user2,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Sell",
        price=100.00,  # Lower price
        quantity=50,
        status="Pending"
    )
    market_buy_order = Orders.objects.create(
        user=user1,
        stock=stock,
        stock_symbol="TCH",
        order_type="Market",  # Market order
        action="Buy",
        quantity=60,  # Wants to buy 60 shares
        status="Pending"
    )
    print(f"Market Buy Order Executed: {market_buy_order}")

    # Test Case 2: Limit Buy Order
    print("\nTest Case 2: Limit Buy Order")
    Orders.objects.create(
        user=user2,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Sell",
        price=102.00,
        quantity=50,
        status="Pending"
    )
    Orders.objects.create(
        user=user2,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Sell",
        price=100.00,
        quantity=50,
        status="Pending"
    )
    limit_buy_order = Orders.objects.create(
        user=user1,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Buy",
        price=101.00,  # Will only match sell orders priced <= 101.00
        quantity=70,
        status="Pending"
    )
    print(f"Limit Buy Order Executed: {limit_buy_order}")

    # Test Case 3: Market Sell Order
    print("\nTest Case 3: Market Sell Order")
    Orders.objects.create(
        user=user1,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Buy",
        price=103.00,
        quantity=30,
        status="Pending"
    )
    Orders.objects.create(
        user=user1,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Buy",
        price=101.00,
        quantity=20,
        status="Pending"
    )
    market_sell_order = Orders.objects.create(
        user=user2,
        stock=stock,
        stock_symbol="TCH",
        order_type="Market",  # Market order
        action="Sell",
        quantity=40,  # Wants to sell 40 shares
        status="Pending"
    )
    print(f"Market Sell Order Executed: {market_sell_order}")

    # Test Case 4: Limit Sell Order
    print("\nTest Case 4: Limit Sell Order")
    Orders.objects.create(
        user=user1,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Buy",
        price=105.00,
        quantity=30,
        status="Pending"
    )
    Orders.objects.create(
        user=user1,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Buy",
        price=100.00,
        quantity=20,
        status="Pending"
    )
    limit_sell_order = Orders.objects.create(
        user=user2,
        stock=stock,
        stock_symbol="TCH",
        order_type="Limit",  # Limit order
        action="Sell",
        price=102.00,  # Will only match buy orders priced >= 102.00
        quantity=40,
        status="Pending"
    )
    print(f"Limit Sell Order Executed: {limit_sell_order}")
