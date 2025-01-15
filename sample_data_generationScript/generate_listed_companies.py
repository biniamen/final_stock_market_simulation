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
    conn = psycopg2.connect(
        dbname=DATABASES['NAME'],
        user=DATABASES['USER'],
        password=DATABASES['PASSWORD'],
        host=DATABASES['HOST'],
        port=DATABASES['PORT']
    )
    return conn

# Generate and insert companies into the database
def generate_and_insert_companies(conn):
    cursor = conn.cursor()

    # Fetch existing companies to avoid duplication
    cursor.execute("SELECT company_name FROM stocks_listedcompany;")
    existing_companies = {row[0] for row in cursor.fetchall()}

    for company_name, sector in ethiopian_companies:
        if company_name in existing_companies:
            continue  # Skip if the company already exists

        # Insert into ListedCompany table
        cursor.execute("""
            INSERT INTO stocks_listedcompany (company_name, sector, last_updated)
            VALUES (%s, %s, NOW());
        """, (company_name, sector))

    conn.commit()
    print("Companies inserted successfully.")
    cursor.close()

# Main function to generate and insert listed companies
def generate_and_insert_data():
    conn = connect_to_db()
    try:
        generate_and_insert_companies(conn)
    finally:
        conn.close()

# Execute script
generate_and_insert_data()
