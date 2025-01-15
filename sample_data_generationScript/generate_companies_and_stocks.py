import numpy as np
import psycopg2
from datetime import datetime
from decimal import Decimal

# Database connection settings
DATABASES = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'ethio_stock_simulation_db',
    'USER': 'stock_user',
    'PASSWORD': 'Amen@2461',
    'HOST': 'localhost',
    'PORT': '5432',
}

# List of Ethiopian companies and sectors
ethiopian_companies = [
    ("Ethio Telecom", "Telecommunications"),
    ("Ovid Real Estate", "Construction"),
    ("Ethiopian Sugar Corporation", "Agriculture"),
    ("Commercial Bank of Ethiopia", "Banking"),
    ("Awash Bank", "Banking"),
    ("Dashen Bank", "Banking"),
    ("Bank of Abyssinia", "Banking"),
    ("Ayat Real Estate", "Construction"),
    ("Wegagen Bank", "Banking"),
    ("Nib International Bank", "Banking"),
    ("Berhan International Bank", "Banking"),
    ("Ethiopian Airlines", "Airlines"),
    ("Habesha Breweries", "Breweries"),
    ("Meta Brewery", "Breweries"),
    ("Ethiopian Shipping Lines", "Shipping"),
    ("MIDROC Ethiopia", "Manufacturing"),
    ("Anbessa City Bus", "Transport"),
    ("Ethiopian Electric Power", "Energy"),
    ("Amhara Bank", "Banking"),
    ("Enat Bank", "Banking"),
    ("Bunna Insurance", "Insurance"),
    ("Ethio Cement", "Manufacturing"),
]

# Connect to the database
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DATABASES['NAME'],
            user=DATABASES['USER'],
            password=DATABASES['PASSWORD'],
            host=DATABASES['HOST'],
            port=DATABASES['PORT']
        )
        print("Database connection established.")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise

# Generate unique ticker symbol
def generate_ticker_symbol(company_name, existing_symbols):
    # Extract first letters of each word to form the base ticker
    base_ticker = "".join(word[0] for word in company_name.split())[:4].upper()
    if len(base_ticker) < 4:
        # Pad with 'X' if less than 4 characters
        base_ticker = base_ticker.ljust(4, 'X')
    ticker_symbol = base_ticker
    counter = 1
    while ticker_symbol in existing_symbols:
        # Modify the base ticker to ensure uniqueness
        ticker_symbol = f"{base_ticker[:3]}{counter}"
        ticker_symbol = ticker_symbol[:4]
        counter += 1
    return ticker_symbol

# Generate and insert companies and stocks into the database
def generate_and_insert_companies_and_stocks(conn):
    cursor = conn.cursor()
    try:
        # Fetch existing companies and their IDs
        cursor.execute("SELECT id, company_name FROM stocks_listedcompany;")
        existing_companies = {row[1]: row[0] for row in cursor.fetchall()}
        print(f"Fetched {len(existing_companies)} existing companies.")

        # Fetch existing ticker symbols to avoid duplication
        cursor.execute("SELECT ticker_symbol FROM stocks_stocks;")
        existing_ticker_symbols = {row[0] for row in cursor.fetchall()}
        print(f"Fetched {len(existing_ticker_symbols)} existing ticker symbols.")

        # Fetch existing stocks to identify which companies already have stocks
        cursor.execute("SELECT company_id FROM stocks_stocks;")
        existing_stock_company_ids = {row[0] for row in cursor.fetchall()}
        print(f"Fetched {len(existing_stock_company_ids)} existing stock entries.")

        new_companies_count = 0
        new_stocks_count = 0

        for company_name, sector in ethiopian_companies:
            if company_name in existing_companies:
                company_id = existing_companies[company_name]
                company_exists = True
                print(f"Company '{company_name}' already exists with ID {company_id}.")
            else:
                # Insert the company into the ListedCompany table
                try:
                    cursor.execute("""
                        INSERT INTO stocks_listedcompany (company_name, sector, last_updated)
                        VALUES (%s, %s, NOW())
                        RETURNING id;
                    """, (company_name, sector))
                    company_id = cursor.fetchone()[0]
                    existing_companies[company_name] = company_id
                    new_companies_count += 1
                    print(f"Inserted new company '{company_name}' with ID {company_id}.")
                    company_exists = False
                except psycopg2.Error as e:
                    print(f"Error inserting company '{company_name}': {e}")
                    conn.rollback()
                    continue  # Skip to next company

            # Check if stock exists for this company
            if company_id in existing_stock_company_ids:
                print(f"Stock for company '{company_name}' (ID: {company_id}) already exists. Skipping stock insertion.")
                continue  # Stock already exists

            # Generate stock data
            try:
                # Generate stock price using normal distribution
                stock_price = Decimal(str(round(np.random.normal(loc=1150, scale=150), 2)))
                stock_price = max(800, min(stock_price, 1500))  # Clamp between 800 and 1500
                print(f"Generated stock price for '{company_name}': {stock_price} Birr")

                # Calculate total shares inversely proportional to stock price
                # Ensure stock_price is not zero to avoid division by zero
                if stock_price == 0:
                    print(f"Stock price for '{company_name}' is zero. Skipping stock insertion.")
                    continue

                total_shares = int(1_000_000 * (1500 / float(stock_price)))
                total_shares = max(total_shares, 1)  # Ensure at least 1 share
                available_shares = total_shares
                max_trading_limit = int(total_shares * 0.25)
                print(f"Total shares for '{company_name}': {total_shares}")
                print(f"Max trading limit for '{company_name}': {max_trading_limit}")

                # Generate unique ticker symbol
                ticker_symbol = generate_ticker_symbol(company_name, existing_ticker_symbols)
                existing_ticker_symbols.add(ticker_symbol)
                print(f"Generated ticker symbol for '{company_name}': {ticker_symbol}")

                # Insert stock data into Stocks table
                cursor.execute("""
                    INSERT INTO stocks_stocks (
                        company_id, ticker_symbol, total_shares, available_shares, 
                        current_price, max_trader_buy_limit, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, NOW());
                """, (
                    company_id, ticker_symbol, total_shares, available_shares, 
                    stock_price, max_trading_limit
                ))
                new_stocks_count += 1
                print(f"Inserted stock for company '{company_name}' (ID: {company_id}) with ticker '{ticker_symbol}'.")
            except psycopg2.Error as e:
                print(f"Error inserting stock for company '{company_name}': {e}")
                conn.rollback()
                continue  # Skip to next company

        conn.commit()
        print(f"Inserted {new_companies_count} new companies and {new_stocks_count} new stocks successfully.")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()

# Main function to execute the script
def generate_and_insert_data():
    conn = None
    try:
        conn = connect_to_db()
        generate_and_insert_companies_and_stocks(conn)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# Execute script
if __name__ == "__main__":
    generate_and_insert_data()
