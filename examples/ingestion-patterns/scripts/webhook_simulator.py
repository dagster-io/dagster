#!/usr/bin/env python3
import argparse
import random
import time
import uuid
from datetime import datetime

from ingestion_patterns.resources.mock_apis import get_webhook_storage, receive_webhook


def create_webhook_payload(event_num: int) -> dict:
    """Generate a sample webhook payload."""
    event_types = ["order.created", "order.updated", "payment.completed", "user.signup"]

    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "data": {
            "event_type": random.choice(event_types),
            "event_num": event_num,
            "amount": round(random.uniform(10.0, 500.0), 2),
            "customer_id": f"cust-{random.randint(1, 100):03d}",
            "metadata": {
                "source": "webhook-simulator",
                "version": "1.0",
            },
        },
    }


def simulate_webhooks(
    source_id: str,
    count: int,
    interval: float,
) -> None:
    """Simulate webhook pushes to the storage buffer."""
    print(f"Simulating {count} webhook pushes for source '{source_id}'...")  # noqa: T201
    print(f"Interval between events: {interval}s")  # noqa: T201
    print("-" * 50)  # noqa: T201

    for i in range(1, count + 1):
        payload = create_webhook_payload(i)
        receive_webhook(source_id, payload)

        print(  # noqa: T201
            f"[{i}/{count}] Pushed webhook: id={payload['id'][:8]}... "
            f"type={payload['data']['event_type']}"
        )

        if interval > 0 and i < count:
            time.sleep(interval)

    # Show storage state
    storage = get_webhook_storage()
    pending_count = len(storage.get(source_id, []))

    print("-" * 50)  # noqa: T201
    print(f"Simulated {count} webhook pushes successfully!")  # noqa: T201
    print(f"Pending payloads in storage for '{source_id}': {pending_count}")  # noqa: T201
    print("\nTo process these payloads, materialize the 'process_webhook_data' asset")  # noqa: T201
    print(f"with config: source_id='{source_id}'")  # noqa: T201


def main():
    parser = argparse.ArgumentParser(description="Simulate webhook pushes for testing")
    parser.add_argument(
        "--source",
        default="default",
        help="Source ID for the webhooks (default: default)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of webhooks to simulate (default: 10)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Interval between webhooks in seconds (default: 0.1)",
    )

    args = parser.parse_args()

    simulate_webhooks(args.source, args.count, args.interval)


if __name__ == "__main__":
    main()
