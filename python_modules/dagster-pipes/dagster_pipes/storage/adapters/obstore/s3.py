"""S3 storage adapter using obstore."""

from typing import Any, Optional

from obstore.store import S3Store

from dagster_pipes.storage.adapters.obstore.base import ObjectStoreAdapter


class S3StorageAdapter(ObjectStoreAdapter):
    """Storage adapter for Amazon S3 and S3-compatible storage.

    Uses obstore for high-performance S3 operations. Credentials are loaded from
    environment variables by default (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.)
    but can be explicitly provided.

    Example:
        >>> from dagster_pipes.storage import StorageAddress, StorageAdapterRegistry
        >>> from dagster_pipes.storage.adapters.obstore.s3 import S3StorageAdapter
        >>> import pandas as pd
        >>>
        >>> # Using environment credentials
        >>> adapter = S3StorageAdapter(bucket="my-bucket")
        >>> registry = StorageAdapterRegistry([adapter])
        >>>
        >>> # Load a parquet file
        >>> df = registry.load(StorageAddress("s3", "path/to/data.parquet"), pd.DataFrame)
        >>>
        >>> # Store data
        >>> registry.store(df, StorageAddress("s3", "path/to/output.parquet"))
        >>>
        >>> # With explicit credentials
        >>> adapter = S3StorageAdapter(
        ...     bucket="my-bucket",
        ...     region="us-west-2",
        ...     access_key_id="AKIA...",
        ...     secret_access_key="...",
        ... )
        >>>
        >>> # For S3-compatible storage (MinIO, etc.)
        >>> adapter = S3StorageAdapter(
        ...     bucket="my-bucket",
        ...     endpoint_url="http://localhost:9000",
        ...     access_key_id="minioadmin",
        ...     secret_access_key="minioadmin",
        ... )
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        session_token: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        skip_signature: bool = False,
        **kwargs: Any,
    ):
        """Initialize the S3 adapter.

        Args:
            bucket: S3 bucket name. Falls back to AWS_BUCKET or AWS_BUCKET_NAME env var.
            region: AWS region. Falls back to AWS_REGION env var (default: us-east-1).
            access_key_id: AWS access key. Falls back to AWS_ACCESS_KEY_ID env var.
            secret_access_key: AWS secret key. Falls back to AWS_SECRET_ACCESS_KEY env var.
            session_token: AWS session token. Falls back to AWS_SESSION_TOKEN env var.
            endpoint_url: Custom endpoint for S3-compatible storage (MinIO, etc.).
                Falls back to AWS_ENDPOINT_URL env var.
            skip_signature: Set True for public buckets (no credentials needed).
            **kwargs: Additional arguments passed to S3Store.
        """
        super().__init__()
        self._bucket = bucket
        self._region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._session_token = session_token
        self._endpoint_url = endpoint_url
        self._skip_signature = skip_signature
        self._extra_kwargs = kwargs

    @property
    def storage_type(self) -> str:
        return "s3"

    def _create_store(self) -> S3Store:
        """Create the S3Store instance."""
        kwargs: dict[str, Any] = {}

        if self._bucket is not None:
            kwargs["bucket"] = self._bucket
        if self._region is not None:
            kwargs["region"] = self._region
        if self._access_key_id is not None:
            kwargs["access_key_id"] = self._access_key_id
        if self._secret_access_key is not None:
            kwargs["secret_access_key"] = self._secret_access_key
        if self._session_token is not None:
            kwargs["session_token"] = self._session_token
        if self._endpoint_url is not None:
            kwargs["endpoint"] = self._endpoint_url
        if self._skip_signature:
            kwargs["skip_signature"] = True

        kwargs.update(self._extra_kwargs)

        return S3Store(**kwargs)
