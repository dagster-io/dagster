#!/usr/bin/env python3
"""Simulate webhook pushes directly to the file storage.

This script writes webhook payloads directly to the shared storage directory,
simulating what the webhook server does when it receives HTTP requests.
"""

import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

# Default storage directory (same as webhook server and Dagster resource)
WEBHOOK_STORAGE_DIR = Path(os.environ.get("WEBHOOK_STORAGE_DIR", "/tmp/webhook_storage"))


def ensure_storage_dir() -> None:
    """Ensure the storage directory exists."""
    WEBHOOK_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def receive_webhook(source_id: str, payload: dict) -> None:
    """Store a webhook payload to file storage."""
    ensure_storage_dir()

    # Add metadata
    payload["received_at"] = datetime.now().isoformat()

    # Load existing payloads
    source_file = WEBHOOK_STORAGE_DIR / f"{source_id}.json"
    existing: list = []
    if source_file.exists():
        with open(source_file) as f:
            existing = json.load(f)

    # Append new payload
    existing.append(payload)

    # Save back
    with open(source_file, "w") as f:
        json.dump(existing, f, indent=2)


def get_pending_count(source_id: str) -> int:
    """Get count of pending payloads for a source."""
    source_file = WEBHOOK_STORAGE_DIR / f"{source_id}.json"
    if not source_file.exists():
        return 0
    with open(source_file) as f:
        return len(json.load(f))


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
    print(f"Storage directory: {WEBHOOK_STORAGE_DIR}")  # noqa: T201
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
    pending_count = get_pending_count(source_id)

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
