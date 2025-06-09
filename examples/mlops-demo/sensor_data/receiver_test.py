import polars as pl
import pika
import time
import argparse

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.basic_consume(queue="failures", auto_ack=True, on_message_callback=callback)

channel.start_consuming()

