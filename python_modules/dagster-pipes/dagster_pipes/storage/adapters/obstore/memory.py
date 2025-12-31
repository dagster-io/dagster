"""In-memory storage adapter using obstore (for testing)."""

from obstore.store import MemoryStore

from dagster_pipes.storage.adapters.obstore.base import ObjectStoreAdapter


class MemoryStorageAdapter(ObjectStoreAdapter):
    """In-memory storage adapter for testing.

    Uses obstore's MemoryStore for isolated testing without cloud credentials.

    Example:
        >>> from dagster_pipes.storage import StorageAddress, StorageAdapterRegistry
        >>> from dagster_pipes.storage.adapters.obstore.memory import MemoryStorageAdapter
        >>> import pandas as pd
        >>>
        >>> adapter = MemoryStorageAdapter()
        >>> registry = StorageAdapterRegistry([adapter])
        >>>
        >>> # Store and load data
        >>> df = pd.DataFrame({"a": [1, 2, 3]})
        >>> registry.store(df, StorageAddress("memory", "test.parquet"))
        >>> loaded = registry.load(StorageAddress("memory", "test.parquet"), pd.DataFrame)
    """

    def __init__(self):
        super().__init__()

    @property
    def storage_type(self) -> str:
        return "memory"

    def _create_store(self) -> MemoryStore:
        """Create an in-memory store."""
        return MemoryStore()
