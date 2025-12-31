"""Local filesystem storage adapter using obstore."""

from pathlib import Path

from obstore.store import LocalStore

from dagster_pipes.storage.adapters.obstore.base import ObjectStoreAdapter


class LocalStorageAdapter(ObjectStoreAdapter):
    """Local filesystem storage adapter.

    Uses obstore's LocalStore for local file operations with the same
    interface as cloud storage adapters.

    Args:
        prefix: Root directory for storage. Defaults to current directory.
        mkdir: If True and prefix is provided, create the directory if needed.

    Example:
        >>> from dagster_pipes.storage import StorageAddress, StorageAdapterRegistry
        >>> from dagster_pipes.storage.adapters.obstore.local import LocalStorageAdapter
        >>> import pandas as pd
        >>>
        >>> adapter = LocalStorageAdapter(prefix="/tmp/data", mkdir=True)
        >>> registry = StorageAdapterRegistry([adapter])
        >>>
        >>> # Store and load data
        >>> df = pd.DataFrame({"a": [1, 2, 3]})
        >>> registry.store(df, StorageAddress("local", "test.parquet"))
        >>> loaded = registry.load(StorageAddress("local", "test.parquet"), pd.DataFrame)
    """

    def __init__(self, prefix: str | Path | None = None, mkdir: bool = False):
        super().__init__()
        self._prefix = prefix
        self._mkdir = mkdir

    @property
    def storage_type(self) -> str:
        return "local"

    def _create_store(self) -> LocalStore:
        """Create a local filesystem store."""
        return LocalStore(prefix=self._prefix, mkdir=self._mkdir)
