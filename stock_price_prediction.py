import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from tensorflow.keras.models import load_model
import schedule
import time

# Database connection
engine = create_engine("postgresql://username:password@localhost:5432/stock_market_db")

# Fetch and preprocess data
def fetch_data():
    query = """
    SELECT 
        stock_id,
        MIN(price) AS opening_price,
        MAX(price) AS closing_price,
        MAX(price) AS high_price,
        MIN(price) AS low_price,
        SUM(quantity) AS total_volume,
        AVG(price) AS average_price,
        CURRENT_DATE AS date
    FROM stocks_trade
    WHERE trade_time >= CURRENT_DATE AND trade_time < CURRENT_DATE + INTERVAL '1 day'
    GROUP BY stock_id;
    """
    df = pd.read_sql_query(query, engine)

    # Add external factors
    df['currency_rate'] = 55.50  # Example rate, replace with API call if needed
    df['sentiment_score'] = np.random.uniform(-1, 1, size=len(df))  # Dummy sentiment score
    return df

# Predict stock prices using LSTM
def predict_stock_prices(df):
    # Load the LSTM model
    model = load_model("lstm_model.h5")

    # Prepare data for prediction
    features = df[['opening_price', 'closing_price', 'high_price', 'low_price', 
                   'total_volume', 'currency_rate', 'sentiment_score']].values
    features = features.reshape((features.shape[0], 1, features.shape[1]))  # Reshape for LSTM

    # Predict prices
    predicted_prices = model.predict(features)

    # Add predictions to the data
    df['predicted_price'] = predicted_prices.flatten()
    return df

# Update stock prices in the database
def update_prices(data):
    for index, row in data.iterrows():
        query = """
        UPDATE stocks_stocks
        SET current_price = %s
        WHERE id = %s;
        """
        engine.execute(query, (row['predicted_price'], row['stock_id']))

# Update trader portfolios
def update_portfolio(data):
    for index, row in data.iterrows():
        query = """
        UPDATE trader_portfolios
        SET total_investment = total_quantity * %s,
            average_purchase_price = total_investment / total_quantity
        WHERE stock_id = %s;
        """
        engine.execute(query, (row['predicted_price'], row['stock_id']))

# Main function
def daily_task():
    print("Starting stock price prediction task...")
    data = fetch_data()
    data = predict_stock_prices(data)
    update_prices(data)
    update_portfolio(data)
    print("Task completed successfully!")

# Schedule the task
schedule.every().day.at("17:00").do(daily_task)  # Run daily at 5 PM

# Keep the scheduler running
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
