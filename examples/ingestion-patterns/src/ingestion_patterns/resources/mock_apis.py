import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# File-based storage for webhook payloads (works across processes)
WEBHOOK_STORAGE_DIR = Path(os.environ.get("WEBHOOK_STORAGE_DIR", "/tmp/dagster_webhook_storage"))


def _ensure_storage_dir() -> None:
    """Ensure the storage directory exists."""
    WEBHOOK_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_source_id(source_id: str) -> str:
    """Sanitize source_id to prevent path traversal attacks.

    Only allows alphanumeric characters, hyphens, and underscores.

    Args:
        source_id: The source identifier from user input.

    Returns:
        Sanitized source_id safe for use in filenames.

    Raises:
        ValueError: If source_id is invalid after sanitization.
    """
    # Allow only alphanumeric, hyphens, and underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", source_id)

    if not sanitized:
        raise ValueError("Invalid source_id: must contain valid filename characters")

    return sanitized


def _get_source_file(source_id: str) -> Path:
    """Get the file path for a source's payloads with path traversal protection.

    Args:
        source_id: The source identifier from user input.

    Returns:
        The validated file path within WEBHOOK_STORAGE_DIR.

    Raises:
        ValueError: If source_id would result in path traversal.
    """
    # Sanitize the source_id
    safe_id = _sanitize_source_id(source_id)

    # Construct the path
    source_file = WEBHOOK_STORAGE_DIR / f"{safe_id}.json"

    # Resolve to absolute path and verify it's within the storage directory
    resolved_path = source_file.resolve()
    resolved_storage = WEBHOOK_STORAGE_DIR.resolve()

    if not str(resolved_path).startswith(str(resolved_storage) + os.sep):
        raise ValueError("Invalid source_id: path traversal detected")

    return resolved_path


def get_webhook_storage() -> dict[str, list[dict[str, Any]]]:
    """Get all webhook payloads from file storage."""
    _ensure_storage_dir()
    storage: dict[str, list[dict[str, Any]]] = {}

    for source_file in WEBHOOK_STORAGE_DIR.glob("*.json"):
        source_id = source_file.stem
        with open(source_file) as f:
            storage[source_id] = json.load(f)

    return storage


def receive_webhook(source_id: str, payload: dict[str, Any]) -> None:
    """Store a webhook payload to file storage.

    Works across processes since it uses file-based storage.
    """
    _ensure_storage_dir()

    # Add metadata
    payload["received_at"] = datetime.now().isoformat()

    # Load existing payloads
    source_file = _get_source_file(source_id)
    existing: list[dict[str, Any]] = []
    if source_file.exists():
        with open(source_file) as f:
            existing = json.load(f)

    # Append new payload
    existing.append(payload)

    # Save back
    with open(source_file, "w") as f:
        json.dump(existing, f, indent=2)


def clear_webhook_storage(source_id: str) -> None:
    """Clear all payloads for a source."""
    source_file = _get_source_file(source_id)
    if source_file.exists():
        source_file.unlink()


class MockAPIClient:
    """Mock API client for pull-based ingestion."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._data = self._generate_mock_data()

    def _generate_mock_data(self) -> list[dict[str, Any]]:
        """Generate mock data for demonstration."""
        base_time = datetime.now() - timedelta(days=7)
        data = []
        for i in range(100):
            data.append(
                {
                    "id": f"record-{i:03d}",
                    "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                    "value": 100 + i * 10,
                    "status": "active" if i % 2 == 0 else "inactive",
                }
            )
        return data

    def get_records(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        """Simulate API call to get records in date range."""
        filtered = [
            record
            for record in self._data
            if start_date <= datetime.fromisoformat(record["timestamp"]) < end_date
        ]
        return filtered


class MockKafkaConsumer:
    """Mock Kafka consumer for polling-based ingestion."""

    def __init__(self, topic: str, consumer_group: str):
        self.topic = topic
        self.consumer_group = consumer_group
        self._messages = self._generate_mock_messages()
        self._current_offset = -1

    def _generate_mock_messages(self) -> list[dict[str, Any]]:
        """Generate mock messages for demonstration."""
        messages = []
        base_time = datetime.now()
        for i in range(50):
            messages.append(
                {
                    "offset": i,
                    "partition": 0,
                    "timestamp": int((base_time.timestamp() + i * 60) * 1000),
                    "key": f"key-{i:03d}",
                    "value": json.dumps(
                        {
                            "event_id": f"event-{i:03d}",
                            "event_type": "transaction",
                            "amount": 100 + i * 5,
                            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                        }
                    ),
                }
            )
        return messages

    def seek(self, offset: int) -> None:
        """Seek to a specific offset."""
        self._current_offset = offset - 1

    def poll(self, timeout_ms: int = 1000, max_records: int = 100) -> list[dict[str, Any]]:
        """Poll for new messages."""
        messages = []
        start_offset = self._current_offset + 1

        for msg in self._messages:
            if msg["offset"] < start_offset:
                continue
            if len(messages) >= max_records:
                break
            messages.append(msg)
            self._current_offset = msg["offset"]

        return messages

    def close(self) -> None:
        """Close the consumer."""
        pass
