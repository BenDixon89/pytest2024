import pika
import json

def send_change_request(coin_denominations, purchase_amount, tender_amount):
    url = 'amqp://guest:guest@4.250.233.128:5672/'
    parameters = pika.URLParameters(url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='change_queue')

    message = {
        'coin_denominations': coin_denominations,
        'purchase_amount': purchase_amount,
        'tender_amount': tender_amount
    }

    channel.basic_publish(
        exchange='',
        routing_key='change_queue',
        body=json.dumps(message)
    )

    print(" [x] Sent change request")

    connection.close()

# Example usage
if __name__ == "__main__":
    send_change_request([1, 5, 10, 25], 1.35, 2.00)
