"""Tests for StorageAddress."""


def test_storage_address():
    """Test StorageAddress basic functionality."""
    from dagster_pipes.storage import StorageAddress

    addr = StorageAddress("duckdb", "my_schema.my_table")
    assert addr.storage_type == "duckdb"
    assert addr.address == "my_schema.my_table"
    assert addr.metadata == {}


def test_storage_address_with_metadata():
    """Test StorageAddress with metadata."""
    from dagster_pipes.storage import StorageAddress

    addr = StorageAddress("s3", "bucket/path/file.parquet", metadata={"format": "parquet"})
    assert addr.storage_type == "s3"
    assert addr.address == "bucket/path/file.parquet"
    assert addr.metadata == {"format": "parquet"}


def test_storage_address_immutable():
    """Test StorageAddress is immutable (frozen dataclass)."""
    import pytest
    from dagster_pipes.storage import StorageAddress

    addr = StorageAddress("s3", "bucket/path")
    with pytest.raises(AttributeError):
        addr.storage_type = "gcs"  # type: ignore
