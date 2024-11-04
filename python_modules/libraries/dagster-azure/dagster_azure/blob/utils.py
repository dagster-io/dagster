import warnings

try:
    # Centralise Azure imports here so we only need to warn in one place
    from azure.core.exceptions import ResourceNotFoundError
    from azure.storage.blob import BlobServiceClient, generate_blob_sas
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


def _create_url(storage_account, subdomain, cloud_type: str = "public"):
    if cloud_type == "public":
        return f"https://{storage_account}.{subdomain}.core.windows.net/"
    elif cloud_type == "government":
        return f"https://{storage_account}.{subdomain}.core.usgovcloudapi.net/"
    else:
        raise ValueError(f"Unsupported cloud_type: {cloud_type}")


def create_blob_client(
    storage_account, credential, cloud_type: str = "public"
) -> BlobServiceClient:
    """Create a Blob Storage client."""
    account_url = _create_url(storage_account, "blob", cloud_type)
    if hasattr(credential, "account_key"):
        credential = credential.account_key
    return BlobServiceClient(account_url, credential)


__all__ = ["create_blob_client", "generate_blob_sas", "BlobServiceClient", "ResourceNotFoundError"]
