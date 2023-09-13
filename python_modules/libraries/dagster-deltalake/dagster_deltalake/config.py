import sys
from typing import Optional

from dagster import Config

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class LocalConfig(Config):
    """Storage configuration for local object store."""

    provider: Literal["local"] = "local"


class AzureConfig(Config):
    """Storage configuration for Microsoft Azure Blob or ADLS Gen 2 object store."""

    provider: Literal["azure"] = "azure"

    account_name: str
    """Storage account name"""

    client_id: Optional[str]
    """Client ID for ID / secret based authentication."""

    client_secret: Optional[str]
    """Client secret for ID / secret based authentication."""

    tenant_id: Optional[str]
    """Tenant ID for ID / secret based authentication."""

    federated_token_file: Optional[str]
    """File containing federated credential token"""

    account_key: Optional[str]
    """Storage account master key"""

    sas_key: Optional[str]
    """Shared access signature"""

    token: Optional[str]
    """Hard-coded bearer token"""

    msi_resource_id: Optional[str]


class S3Config(Config):
    """Storage configuration for Amazon Web Services (AWS) S3 object store."""

    provider: Literal["s3"] = "s3"

    access_key_id: Optional[str]
    """AWS access key ID"""

    secret_access_key: Optional[str]
    """AWS access key secret"""

    default_region: Optional[str]
    bucket: Optional[str]
    endpoint: Optional[str]
    session_token: Optional[str]
    imdsv1_fallback: bool = False
    virtual_hosted_style_request: Optional[str]
    """Bucket is hosted under virtual-hosted-style URL"""

    metadata_endpoint: Optional[str]
    """Instance metadata endpoint URL for fetching credentials"""

    profile: Optional[str]
