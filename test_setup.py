from stocks.models import ListedCompany, Stocks, UsersPortfolio, Orders
from django.contrib.auth import get_user_model

# Get the User model
User = get_user_model()

def setup_test_environment():
    # Create a company
    company = ListedCompany.objects.create(company_name="TechCorp", sector="Technology")

    # Create a stock
    stock = Stocks.objects.create(
        company=company,
        ticker_symbol="TCH",
        total_shares=1000,
        available_shares=500,
        current_price=100.00
    )
    print(f"Created stock: {stock}")

    # Create two users
    user1 = User.objects.create_user(username="buyer", password="password123")
    user2 = User.objects.create_user(username="seller", password="password123")

    # Create portfolios for the users
    UsersPortfolio.objects.create(user=user1, quantity=0, total_investment=0.00)
    UsersPortfolio.objects.create(user=user2, quantity=100, total_investment=10000.00)  # Seller owns 100 shares

    print(f"Created users: {user1.username}, {user2.username}")

    return stock, user1, user2
