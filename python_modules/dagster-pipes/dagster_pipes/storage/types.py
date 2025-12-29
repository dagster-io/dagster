from dataclasses import dataclass, field
from typing import Any


class StorageError(Exception):
    """Base exception for storage operations.

    Raised when storage operations fail due to adapter lookup failures,
    serialization errors, or other storage-related issues.
    """

    pass


@dataclass(frozen=True)
class StorageAddress:
    """Identifies a storage location with optional metadata.

    Args:
        storage_type: The type of storage (e.g., "duckdb", "snowflake", "s3")
        address: The address within that storage (e.g., "schema.table", "bucket/path/file.parquet")
        metadata: Optional metadata dict (e.g., {"format": "parquet"})
    """

    storage_type: str
    address: str
    metadata: dict[str, Any] = field(default_factory=dict)
