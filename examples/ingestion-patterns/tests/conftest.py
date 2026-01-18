"""Test fixtures and mock resources for ingestion-patterns tests."""

import json
from datetime import datetime, timedelta
from typing import Any

import dagster as dg
import pytest


class MockAPIClientResource(dg.ConfigurableResource):
    """Mock API client resource for testing."""

    def get_records(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        """Return mock records for the given date range."""
        base_time = datetime.now() - timedelta(days=7)
        data = []
        for i in range(100):
            record_time = base_time + timedelta(hours=i)
            if start_date <= record_time < end_date:
                data.append(
                    {
                        "id": f"record-{i:03d}",
                        "timestamp": record_time.isoformat(),
                        "value": 100 + i * 10,
                        "status": "active" if i % 2 == 0 else "inactive",
                    }
                )
        return data


class MockKafkaConsumerResource(dg.ConfigurableResource):
    """Mock Kafka consumer resource for testing."""

    def poll_messages(
        self,
        topic: str,
        timeout_seconds: int = 60,
        max_records: int = 100,
        context: dg.AssetExecutionContext | None = None,
    ) -> list[dict[str, Any]]:
        """Return mock Kafka messages."""
        messages = []
        base_time = datetime.now()
        for i in range(min(10, max_records)):
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


class MockWebhookStorageResource(dg.ConfigurableResource):
    """Mock webhook storage resource for testing."""

    _storage: dict[str, list[dict[str, Any]]] = {}

    def get_pending_payloads(self, source_id: str) -> list[dict[str, Any]]:
        """Get pending payloads for a source."""
        return self._storage.get(source_id, [])

    def clear_payloads(self, source_id: str) -> None:
        """Clear payloads for a source."""
        if source_id in self._storage:
            del self._storage[source_id]

    def add_payload(self, source_id: str, payload: dict[str, Any]) -> None:
        """Add a payload for testing purposes."""
        if source_id not in self._storage:
            self._storage[source_id] = []
        self._storage[source_id].append(payload)

    def clear_all(self) -> None:
        """Clear all payloads."""
        self._storage.clear()


@pytest.fixture
def mock_api_client():
    """Fixture providing a mock API client resource."""
    return MockAPIClientResource()


@pytest.fixture
def mock_kafka_consumer():
    """Fixture providing a mock Kafka consumer resource."""
    return MockKafkaConsumerResource()


@pytest.fixture
def mock_webhook_storage():
    """Fixture providing a mock webhook storage resource."""
    resource = MockWebhookStorageResource()
    resource.clear_all()
    return resource
