"""Tests for LocalStorageAdapter (obstore)."""

import pytest
from dagster_pipes.storage.adapters.obstore.local import LocalStorageAdapter

from dagster_pipes_tests.storage.adapters.obstore_base import (
    ObjectStoreAdapterTestBase,
    ObjectStoreRoundtripTestsMixin,
)


class TestLocalStorageAdapter(ObjectStoreAdapterTestBase, ObjectStoreRoundtripTestsMixin):
    """Tests for local filesystem storage adapter.

    Uses a temporary directory for isolated testing.
    """

    storage_type = "local"

    @pytest.fixture
    def adapter(self, tmp_path):
        return LocalStorageAdapter(prefix=tmp_path, mkdir=True)
