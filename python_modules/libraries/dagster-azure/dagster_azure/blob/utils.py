import warnings

from dagster_azure._constants import DEFAULT_AZURE_STORAGE_ENDPOINT_SUFFIX

try:
    # Centralise Azure imports here so we only need to warn in one place
    from azure.core.exceptions import ResourceNotFoundError
    from azure.storage.blob import BlobLeaseClient, BlobServiceClient, generate_blob_sas
except ImportError:
    msg = (
        "Could not import required Azure objects. This probably means you have an old version "
        "of azure-storage-blob installed. dagster-azure requires azure-storage-blob~=12.0.0; "
        "this conflicts with dagster-snowflake which requires azure-storage-blob<12.0.0 and is "
        "incompatible. Please uninstall dagster-snowflake and reinstall dagster-azure to fix "
        "this error."
    )
    warnings.warn(msg)
    raise


def _create_url(
    storage_account: str,
    subdomain: str,
    endpoint_suffix: str = DEFAULT_AZURE_STORAGE_ENDPOINT_SUFFIX,
) -> str:
    return f"https://{storage_account}.{subdomain}.{endpoint_suffix}/"


def create_blob_client(
    storage_account: str,
    credential,
    endpoint_suffix: str = DEFAULT_AZURE_STORAGE_ENDPOINT_SUFFIX,
) -> BlobServiceClient:
    """Create a Blob Storage client."""
    account_url = _create_url(storage_account, "blob", endpoint_suffix)
    if hasattr(credential, "account_key"):
        credential = credential.account_key
    return BlobServiceClient(account_url, credential)


__all__ = [
    "BlobLeaseClient",
    "BlobServiceClient",
    "ResourceNotFoundError",
    "create_blob_client",
    "generate_blob_sas",
]
