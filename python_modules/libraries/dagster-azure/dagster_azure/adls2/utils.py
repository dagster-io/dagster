import warnings

try:
    # Centralise Azure imports here so we only need to warn in one place
    from azure.core.exceptions import ResourceNotFoundError
    from azure.storage.filedatalake import DataLakeServiceClient
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


def _create_url(storage_account, subdomain):
    return f"https://{storage_account}.{subdomain}.core.windows.net/"


def create_adls2_client(storage_account: str, credential) -> DataLakeServiceClient:
    """Create an ADLS2 client."""
    account_url = _create_url(storage_account, "dfs")
    return DataLakeServiceClient(account_url, credential)


__all__ = ["create_adls2_client", "DataLakeServiceClient", "ResourceNotFoundError"]
