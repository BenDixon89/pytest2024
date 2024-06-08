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

def get_user_input():
    try:
        coin_denominations = input("Enter coin denominations as a comma-separated list (e.g., 1,2,5,10): ")
        coin_denominations = list(map(int, coin_denominations.split(',')))

        purchase_amount = float(input("Enter purchase amount (e.g., 5.48): "))
        tender_amount = float(input("Enter tender amount (e.g., 7.00): "))

        return coin_denominations, purchase_amount, tender_amount
    except ValueError as e:
        print(f"Invalid input: {e}")
        return None, None, None

# Example usage
if __name__ == "__main__":
    coin_denominations, purchase_amount, tender_amount = get_user_input()
    if coin_denominations is not None:
        send_change_request(coin_denominations, purchase_amount, tender_amount)
    else:
        print("Failed to get valid inputs.")
