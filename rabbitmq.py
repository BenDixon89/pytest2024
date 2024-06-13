import pika
import json
import logging
import os
from changecalc import calculate_change, get_db_connection, store_database

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RabbitMQ setup
def setup_rabbitmq():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue='change_queue')
        channel.basic_consume(queue='change_queue', on_message_callback=callback, auto_ack=False)
        logger.info("Successfully connected to RabbitMQ and started consuming messages.")
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")

# RabbitMQ consumer callback
def callback(ch, method, properties, body):
    data = json.loads(body)
    coin_denominations = data['coin_denominations']
    purchase_amount = data['purchase_amount']
    tender_amount = data['tender_amount']
    change = calculate_change(coin_denominations, purchase_amount, tender_amount)

    store_database(coin_denominations, purchase_amount, tender_amount, change)

    # Publish calculated change to RabbitMQ
    publish_to_rabbitmq('change_returned', {
        'change': change
    })

    ch.basic_ack(delivery_tag=method.delivery_tag)

# Publish to RabbitMQ
def publish_to_rabbitmq(queue_name, message):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message))
        connection.close()
        logger.info(f"Message published to {queue_name}.")
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Error connecting to RabbitMQ for publishing: {e}")