from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
import pika
import json

app = FastAPI()

DATABASE_URL = "postgresql://username:password@postgresql.default.svc.cluster.local:5432/transactions"
RABBITMQ_URL = "rabbitmq.default.svc.cluster.local"

# Database connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

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

# RabbitMQ consumer
def callback(ch, method, properties, body):
    data = json.loads(body)
    coin_denominations = data['coin_denominations']
    purchase_amount = data['purchase_amount']
    tender_amount = data['tender_amount']
    change = calculate_change(coin_denominations, purchase_amount, tender_amount)
    
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

    ch.basic_ack(delivery_tag=method.delivery_tag)

# RabbitMQ setup
def setup_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue='change_queue')
    channel.basic_consume(queue='change_queue', on_message_callback=callback, auto_ack=False)
    print('Waiting for messages...')
    channel.start_consuming()

# Endpoint to test change calculation
@app.post("/calculate-change/")
def calculate_change_endpoint(change_request: ChangeRequest):
    change = calculate_change(change_request.coin_denominations, change_request.purchase_amount, change_request.tender_amount)
    return {"change": change}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
