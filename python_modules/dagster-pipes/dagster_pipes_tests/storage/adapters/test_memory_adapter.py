"""Tests for MemoryStorageAdapter (obstore)."""

import pytest
from dagster_pipes.storage.adapters.obstore.memory import MemoryStorageAdapter

from dagster_pipes_tests.storage.adapters.obstore_base import (
    ObjectStoreAdapterTestBase,
    ObjectStoreRoundtripTestsMixin,
)


class TestMemoryStorageAdapter(ObjectStoreAdapterTestBase, ObjectStoreRoundtripTestsMixin):
    """Tests for in-memory storage adapter.

    Uses obstore's MemoryStore for full roundtrip testing without cloud credentials.
    """

    storage_type = "memory"

    @pytest.fixture
    def adapter(self):
        return MemoryStorageAdapter()
