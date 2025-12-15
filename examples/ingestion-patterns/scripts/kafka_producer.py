#!/usr/bin/env python3
import argparse
import json
import random
import time
from datetime import datetime

from confluent_kafka import Producer


def create_producer(bootstrap_servers: str = "localhost:9094") -> Producer:
    """Create a Kafka producer."""
    return Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "ingestion-patterns-producer",
        }
    )


def create_transaction_event(event_id: int) -> dict:
    """Generate a sample transaction event."""
    event_types = ["purchase", "refund", "transfer", "deposit", "withdrawal"]
    statuses = ["completed", "pending", "processing"]

    return {
        "event_id": f"event-{event_id:06d}",
        "event_type": random.choice(event_types),
        "amount": round(random.uniform(10.0, 1000.0), 2),
        "currency": "USD",
        "status": random.choice(statuses),
        "customer_id": f"customer-{random.randint(1, 100):03d}",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "source": "test-producer",
            "version": "1.0",
        },
    }


def delivery_callback(err, msg):
    """Callback for message delivery reports."""
    if err is not None:
        print(f"Message delivery failed: {err}")  # noqa: T201
    else:
        print(  # noqa: T201
            f"Message delivered to {msg.topic()} "
            f"[partition {msg.partition()}] @ offset {msg.offset()}"
        )


def produce_events(
    producer: Producer,
    topic: str,
    count: int,
    interval: float,
) -> None:
    """Produce sample events to Kafka."""
    print(f"Producing {count} events to topic '{topic}'...")  # noqa: T201
    print(f"Interval between events: {interval}s")  # noqa: T201
    print("-" * 50)  # noqa: T201

    for i in range(1, count + 1):
        event = create_transaction_event(i)
        key = event["customer_id"]
        value = json.dumps(event)

        producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=delivery_callback,
        )

        # Flush to ensure delivery
        producer.poll(0)

        if interval > 0 and i < count:
            time.sleep(interval)

    # Wait for any outstanding messages to be delivered
    producer.flush()
    print("-" * 50)  # noqa: T201
    print(f"Produced {count} events successfully!")  # noqa: T201


def main():
    parser = argparse.ArgumentParser(description="Produce sample transaction events to Kafka")
    parser.add_argument(
        "--bootstrap-servers",
        default="localhost:9094",
        help="Kafka bootstrap servers (default: localhost:9094)",
    )
    parser.add_argument(
        "--topic",
        default="transactions",
        help="Kafka topic name (default: transactions)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of events to produce (default: 10)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Interval between events in seconds (default: 0.5)",
    )

    args = parser.parse_args()

    producer = create_producer(args.bootstrap_servers)
    produce_events(producer, args.topic, args.count, args.interval)


if __name__ == "__main__":
    main()
