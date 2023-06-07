import sys
from typing import Optional

from dagster import Config

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class LocalConfig(Config):
    """Storage configuration for local objet store."""

    provider: Literal["local"] = "local"


class AzureConfig(Config):
    """Storage configuration for Azure Blob or ADLS Gen 2 objet store."""

    provider: Literal["azure"] = "azure"

    account_name: str
    """Storage account name"""

    client_id: Optional[str]
    """client id for id / secret based authentication."""

    client_secret: Optional[str]
    """client secret for id / secret based authentication."""

    tenant_id: Optional[str]
    """tenant id for id / secret based authentication."""

    federated_token_file: Optional[str]
    """file containing federated credential token"""

    account_key: Optional[str]
    """storage account master key"""

    sas_key: Optional[str]
    """shared access signature"""

    token: Optional[str]
    """hard-coded bearer token"""

    msi_resource_id: Optional[str]


class S3Config(Config):
    """Storage configuration for s3 objet store."""

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
    """Bucket is hosted under virtual-hosted-style url"""

    metadata_endpoint: Optional[str]
    """Instance metadata endpoint url for fetching credentials"""

    profile: Optional[str]
