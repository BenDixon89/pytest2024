import os
import logging
import psycopg2
import json

DATABASE_URL = os.getenv("DATABASE_URL")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Calculate change function
def calculate_change(coin_denominations, purchase_amount, tender_amount):
    change_needed = int(round((tender_amount - purchase_amount) * 100))
    coin_denominations = sorted(coin_denominations, reverse=True)
    change = []
    for coin in coin_denominations:
        while change_needed >= coin:
            change.append(coin)
            change_needed -= coin
    return change

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("Successfully connected to the database.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Error connecting to the database: {e}")
        raise

# Database storage function
def store_database(coin_denominations, purchase_amount, tender_amount, change):
    try:
        # Store transaction in database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO transactions (coin_denominations, purchase_amount, tender_amount, change) VALUES (%s, %s, %s, %s)",
            (json.dumps(coin_denominations), purchase_amount, tender_amount, json.dumps(change))
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Transaction successfully stored in the database.")
        
    except Exception as e:
        logger.error(f"Error storing transaction in the database: {e}")