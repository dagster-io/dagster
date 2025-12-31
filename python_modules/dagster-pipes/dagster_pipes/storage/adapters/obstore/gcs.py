"""Google Cloud Storage adapter using obstore."""

from typing import Any, Optional

from obstore.store import GCSStore

from dagster_pipes.storage.adapters.obstore.base import ObjectStoreAdapter


class GCSStorageAdapter(ObjectStoreAdapter):
    """Storage adapter for Google Cloud Storage.

    Uses obstore for high-performance GCS operations. Credentials are loaded from
    environment variables or application default credentials by default, but can
    be explicitly provided.

    Example:
        >>> from dagster_pipes.storage import StorageAddress, StorageAdapterRegistry
        >>> from dagster_pipes.storage.adapters.obstore.gcs import GCSStorageAdapter
        >>> import pandas as pd
        >>>
        >>> # Using application default credentials
        >>> adapter = GCSStorageAdapter(bucket="my-bucket")
        >>> registry = StorageAdapterRegistry([adapter])
        >>>
        >>> # Load a parquet file
        >>> df = registry.load(StorageAddress("gcs", "path/to/data.parquet"), pd.DataFrame)
        >>>
        >>> # Store data
        >>> registry.store(df, StorageAddress("gcs", "path/to/output.parquet"))
        >>>
        >>> # With explicit service account key
        >>> adapter = GCSStorageAdapter(
        ...     bucket="my-bucket",
        ...     service_account_path="/path/to/service-account.json",
        ... )
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        service_account_path: Optional[str] = None,
        service_account_key: Optional[str] = None,
        application_credentials_path: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the GCS adapter.

        Args:
            bucket: GCS bucket name. Falls back to GOOGLE_BUCKET env var.
            service_account_path: Path to service account JSON file.
                Falls back to GOOGLE_SERVICE_ACCOUNT_PATH env var.
            service_account_key: Service account key as JSON string.
                Falls back to GOOGLE_SERVICE_ACCOUNT_KEY env var.
            application_credentials_path: Path to application credentials.
                Falls back to GOOGLE_APPLICATION_CREDENTIALS env var.
            **kwargs: Additional arguments passed to GCSStore.
        """
        super().__init__()
        self._bucket = bucket
        self._service_account_path = service_account_path
        self._service_account_key = service_account_key
        self._application_credentials_path = application_credentials_path
        self._extra_kwargs = kwargs

    @property
    def storage_type(self) -> str:
        return "gcs"

    def _create_store(self) -> GCSStore:
        """Create the GCSStore instance."""
        kwargs: dict[str, Any] = {}

        if self._bucket is not None:
            kwargs["bucket"] = self._bucket
        if self._service_account_path is not None:
            kwargs["service_account_path"] = self._service_account_path
        if self._service_account_key is not None:
            kwargs["service_account_key"] = self._service_account_key
        if self._application_credentials_path is not None:
            kwargs["application_credentials_path"] = self._application_credentials_path

        kwargs.update(self._extra_kwargs)

        return GCSStore(**kwargs)
