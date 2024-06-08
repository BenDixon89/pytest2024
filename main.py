from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
import pika
import json
import logging
from threading import Thread

app = FastAPI()

DATABASE_URL = "postgresql://username:password@postgresql.default.svc.cluster.local:5432/transactions"
RABBITMQ_URL = "amqp://guest:guest@rabbitmq.default.svc.cluster.local:5672/"

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("Successfully connected to the database.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Error connecting to the database: {e}")
        raise

# Model for the request
class ChangeRequest(BaseModel):
    coin_denominations: List[int]
    purchase_amount: float
    tender_amount: float

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

# RabbitMQ consumer callback
def callback(ch, method, properties, body):
    data = json.loads(body)
    coin_denominations = data['coin_denominations']
    purchase_amount = data['purchase_amount']
    tender_amount = data['tender_amount']
    change = calculate_change(coin_denominations, purchase_amount, tender_amount)
    
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

    ch.basic_ack(delivery_tag=method.delivery_tag)

# RabbitMQ setup
def setup_rabbitmq():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue='change_queue')
        channel.basic_consume(queue='change_queue', on_message_callback=callback, auto_ack=False)
        logger.info("Successfully connected to RabbitMQ and started consuming messages.")
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")

# Register the startup event to start the RabbitMQ consumer
@app.on_event("startup")
def startup_event():
    logger.info("Starting RabbitMQ consumer thread.")
    rabbitmq_thread = Thread(target=setup_rabbitmq)
    rabbitmq_thread.start()

# Endpoint to test change calculation
@app.post("/calculate-change/")
def calculate_change_endpoint(change_request: ChangeRequest):
    change = calculate_change(change_request.coin_denominations, change_request.purchase_amount, change_request.tender_amount)
    return {"change": change}

# Health check endpoint to verify connections
@app.get("/health")
def health_check():
    try:
        # Check database connection
        conn = get_db_connection()
        conn.close()
        db_status = "Database connection successful."
    except Exception as e:
        db_status = f"Database connection error: {e}"

    try:
        # Check RabbitMQ connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_URL))
        connection.close()
        rabbitmq_status = "RabbitMQ connection successful."
    except pika.exceptions.AMQPConnectionError as e:
        rabbitmq_status = f"RabbitMQ connection error: {e}"

    return {"database": db_status, "rabbitmq": rabbitmq_status}

if __name__ == "__main__":
    # Start FastAPI application
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
