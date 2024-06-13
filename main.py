from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
import pika
import json
import logging
import os
from threading import Thread
from rabbitmq import setup_rabbitmq, callback, publish_to_rabbitmq
from changecalc import calculate_change, get_db_connection, store_database

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Model for the request
class ChangeRequest(BaseModel):
    coin_denominations: List[int]
    purchase_amount: float
    tender_amount: float

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
    store_database(change_request.coin_denominations, change_request.purchase_amount, change_request.tender_amount, change)
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
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        connection.close()
        rabbitmq_status = "RabbitMQ connection successful."
    except pika.exceptions.AMQPConnectionError as e:
        rabbitmq_status = f"RabbitMQ connection error: {e}"

    return {"calculation service":"Service running","database": db_status, "rabbitmq": rabbitmq_status}

if __name__ == "__main__":
    # Start FastAPI application
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
