import pika


def callback(ch, method, properties, body):
    print(f" [x] Received {body}")  # noqa


connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

channel.basic_consume(queue="failures", auto_ack=True, on_message_callback=callback)

channel.start_consuming()
