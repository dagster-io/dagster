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

    use_azure_cli: Optional[bool]
    """Use azure cli for acquiring access token"""

    use_fabric_endpoint: Optional[bool]
    """Use object store with url scheme account.dfs.fabric.microsoft.com"""

    msi_resource_id: Optional[str]
    """Msi resource id for use with managed identity authentication."""

    msi_endpoint: Optional[str]
    """Endpoint to request a imds managed identity token."""

    container_name: Optional[str]
    """Storage container name"""


# TODO add documentation and config to handle atomic writes with S3
class S3Config(Config):
    """Storage configuration for Amazon Web Services (AWS) S3 object store."""

    provider: Literal["s3"] = "s3"

    access_key_id: Optional[str]
    """AWS access key ID"""

    secret_access_key: Optional[str]
    """AWS access key secret"""

    region: Optional[str]
    """AWS region"""

    bucket: Optional[str]
    """Storage bucket name"""

    endpoint: Optional[str]
    """Sets custom endpoint for communicating with S3."""

    token: Optional[str]
    """Token to use for requests (passed to underlying provider)"""

    imdsv1_fallback: bool = False
    """Allow fall back to ImdsV1"""

    virtual_hosted_style_request: Optional[str]
    """Bucket is hosted under virtual-hosted-style URL"""

    unsigned_payload: Optional[bool]
    """Avoid computing payload checksum when calculating signature."""

    checksum: Optional[str]
    """Set the checksum algorithm for this client."""

    metadata_endpoint: Optional[str]
    """Instance metadata endpoint URL for fetching credentials"""

    container_credentials_relative_uri: Optional[str]
    """Set the container credentials relative URI
    
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
    """

    copy_if_not_exists: Optional[str]
    """Specifiy additional headers passed to strage backend, that enable 'if_not_exists' semantics.
    
    https://docs.rs/object_store/0.7.0/object_store/aws/enum.S3CopyIfNotExists.html#variant.Header
    """

    allow_unsafe_rename: Optional[bool]
    """Allows tables writes that may conflict with concurrent writers."""


class GcsConfig(Config):
    """Storage configuration for Google Cloud Storage object store."""

    provider: Literal["gcs"] = "gcs"

    service_account: Optional[str]
    """Path to the service account file"""

    service_account_key: Optional[str]
    """The serialized service account key."""

    bucket: Optional[str]
    """Bucket name"""

    application_credentials: Optional[str]
    """Application credentials path"""


class ClientConfig(Config):
    """Configuration for http client interacting with storage APIs."""

    allow_http: Optional[bool]
    """Allow non-TLS, i.e. non-HTTPS connections"""

    allow_invalid_certificates: Optional[bool]
    """Skip certificate validation on https connections.

    ## Warning
    
    You should think very carefully before using this method.
    If invalid certificates are trusted, any certificate for any site will be trusted for use.
    This includes expired certificates. This introduces significant vulnerabilities,
    and should only be used as a last resort or for testing
    """

    connect_timeout: Optional[int]
    """Timeout for only the connect phase of a Client"""

    default_content_type: Optional[str]
    """default CONTENT_TYPE for uploads"""

    http1_only: Optional[bool]
    """Only use http1 connections"""

    http2_keep_alive_interval: Optional[int]
    """Interval for HTTP2 Ping frames should be sent to keep a connection alive."""

    http2_keep_alive_timeout: Optional[int]
    """Timeout for receiving an acknowledgement of the keep-alive ping."""

    http2_keep_alive_while_idle: Optional[int]
    """Enable HTTP2 keep alive pings for idle connections"""

    http2_only: Optional[bool]
    """Only use http2 connections"""

    pool_idle_timeout: Optional[int]
    """The pool max idle timeout

    This is the length of time an idle connection will be kept alive
    """

    pool_max_idle_per_host: Optional[int]
    """maximum number of idle connections per host"""

    proxy_url: Optional[str]
    """HTTP proxy to use for requests"""

    timeout: Optional[int]
    """Request timeout

    The timeout is applied from when the request starts connecting until the response body has finished
    """

    user_agent: Optional[str]
    """User-Agent header to be used by this client"""
