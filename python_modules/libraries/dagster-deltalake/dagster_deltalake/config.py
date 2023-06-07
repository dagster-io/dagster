import sys
from typing import Optional, Union

from dagster import Config
from pydantic import Field
from typing_extensions import Annotated

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class LocalConfig(Config):
    provider: Literal["local"] = "local"


class AzureConfig(Config):
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


class StorageOptions(Config):
    storage_options: Annotated[
        Optional[Union[AzureConfig, S3Config]], Field(discriminator="provider")
    ]
    """Configuration options for accessing storage location"""


class StorageLocation(Config):
    """A Storage location combines a URL with the parameters required to access it.

    Several local and remote object stores are supported. The specific technology is
    identified via the scheme of the URL.

    - local: `file:///<path>` or a relative path
    - s3: s3://<bucket>/<path>
    - azure blob / adls: az://<container>/<path>
    - google: gs://<bucket>/<path>
    """

    url: str
    """A fully qualified path to a storage location"""

    storage_options: Annotated[
        Union[AzureConfig, S3Config, LocalConfig], Field(discriminator="provider")
    ]
    """Configuration options for accessing storage location"""
