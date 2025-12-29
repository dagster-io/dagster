"""Azure Blob Storage adapter using obstore."""

from typing import Any, Optional

from obstore.store import AzureStore

from dagster_pipes.storage.adapters.obstore.base import ObjectStoreAdapter


class AzureBlobStorageAdapter(ObjectStoreAdapter):
    """Storage adapter for Azure Blob Storage.

    Uses obstore for high-performance Azure Blob operations. Credentials are loaded
    from environment variables by default, but can be explicitly provided.

    Example:
        >>> from dagster_pipes.storage import StorageAddress, StorageAdapterRegistry
        >>> from dagster_pipes.storage.adapters.obstore.azure import AzureBlobStorageAdapter
        >>> import pandas as pd
        >>>
        >>> # Using environment credentials (AZURE_STORAGE_ACCOUNT_NAME, etc.)
        >>> adapter = AzureBlobStorageAdapter(container="my-container")
        >>> registry = StorageAdapterRegistry([adapter])
        >>>
        >>> # Load a parquet file
        >>> df = registry.load(StorageAddress("azure", "path/to/data.parquet"), pd.DataFrame)
        >>>
        >>> # Store data
        >>> registry.store(df, StorageAddress("azure", "path/to/output.parquet"))
        >>>
        >>> # With explicit credentials
        >>> adapter = AzureBlobStorageAdapter(
        ...     container="my-container",
        ...     account_name="mystorageaccount",
        ...     account_key="...",
        ... )
    """

    def __init__(
        self,
        container: Optional[str] = None,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        sas_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the Azure Blob Storage adapter.

        Args:
            container: Azure container name. Falls back to AZURE_CONTAINER_NAME env var.
            account_name: Storage account name.
                Falls back to AZURE_STORAGE_ACCOUNT_NAME env var.
            account_key: Storage account key.
                Falls back to AZURE_STORAGE_ACCOUNT_KEY env var.
            sas_token: Shared Access Signature token.
                Falls back to AZURE_STORAGE_SAS_TOKEN env var.
            client_id: Azure AD client ID for service principal auth.
                Falls back to AZURE_CLIENT_ID env var.
            client_secret: Azure AD client secret.
                Falls back to AZURE_CLIENT_SECRET env var.
            tenant_id: Azure AD tenant ID.
                Falls back to AZURE_TENANT_ID env var.
            **kwargs: Additional arguments passed to AzureStore.
        """
        super().__init__()
        self._container = container
        self._account_name = account_name
        self._account_key = account_key
        self._sas_token = sas_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._tenant_id = tenant_id
        self._extra_kwargs = kwargs

    @property
    def storage_type(self) -> str:
        return "azure"

    def _create_store(self) -> AzureStore:
        """Create the AzureStore instance."""
        kwargs: dict[str, Any] = {}

        if self._container is not None:
            kwargs["container"] = self._container
        if self._account_name is not None:
            kwargs["account_name"] = self._account_name
        if self._account_key is not None:
            kwargs["account_key"] = self._account_key
        if self._sas_token is not None:
            kwargs["sas_token"] = self._sas_token
        if self._client_id is not None:
            kwargs["client_id"] = self._client_id
        if self._client_secret is not None:
            kwargs["client_secret"] = self._client_secret
        if self._tenant_id is not None:
            kwargs["tenant_id"] = self._tenant_id

        kwargs.update(self._extra_kwargs)

        return AzureStore(**kwargs)
