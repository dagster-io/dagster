from typing import Literal

from dagster import Config


def _to_str_dict(dictionary: dict) -> dict[str, str]:
    """Filters dict of None values and casts other values to str."""
    return {key: str(value) for key, value in dictionary.items() if value is not None}


class LocalConfig(Config):
    """Storage configuration for local object store."""

    provider: Literal["local"] = "local"

    def str_dict(self) -> dict[str, str]:
        """Storage options as str dict."""
        return _to_str_dict(self.dict())


class AzureConfig(Config):
    """Storage configuration for Microsoft Azure Blob or ADLS Gen 2 object store."""

    provider: Literal["azure"] = "azure"

    account_name: str
    """Storage account name"""

    client_id: str | None = None
    """Client ID for ID / secret based authentication."""

    client_secret: str | None = None
    """Client secret for ID / secret based authentication."""

    tenant_id: str | None = None
    """Tenant ID for ID / secret based authentication."""

    federated_token_file: str | None = None
    """File containing federated credential token"""

    account_key: str | None = None
    """Storage account master key"""

    sas_key: str | None = None
    """Shared access signature"""

    token: str | None = None
    """Hard-coded bearer token"""

    use_azure_cli: bool | None = None
    """Use azure cli for acquiring access token"""

    use_fabric_endpoint: bool | None = None
    """Use object store with url scheme account.dfs.fabric.microsoft.com"""

    msi_resource_id: str | None = None
    """Msi resource id for use with managed identity authentication."""

    msi_endpoint: str | None = None
    """Endpoint to request a imds managed identity token."""

    container_name: str | None = None
    """Storage container name"""

    def str_dict(self) -> dict[str, str]:
        """Storage options as str dict."""
        return _to_str_dict(self.dict())


# TODO add documentation and config to handle atomic writes with S3
class S3Config(Config):
    """Storage configuration for Amazon Web Services (AWS) S3 object store."""

    provider: Literal["s3"] = "s3"

    access_key_id: str | None = None
    """AWS access key ID"""

    secret_access_key: str | None = None
    """AWS access key secret"""

    region: str | None = None
    """AWS region"""

    bucket: str | None = None
    """Storage bucket name"""

    endpoint: str | None = None
    """Sets custom endpoint for communicating with S3."""

    token: str | None = None
    """Token to use for requests (passed to underlying provider)"""

    imdsv1_fallback: bool = False
    """Allow fall back to ImdsV1"""

    virtual_hosted_style_request: str | None = None
    """Bucket is hosted under virtual-hosted-style URL"""

    unsigned_payload: bool | None = None
    """Avoid computing payload checksum when calculating signature."""

    checksum: str | None = None
    """Set the checksum algorithm for this client."""

    metadata_endpoint: str | None = None
    """Instance metadata endpoint URL for fetching credentials"""

    container_credentials_relative_uri: str | None = None
    """Set the container credentials relative URI

    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
    """

    copy_if_not_exists: str | None = None
    """Specifiy additional headers passed to storage backend, that enable 'if_not_exists' semantics.

    https://docs.rs/object_store/0.7.0/object_store/aws/enum.S3CopyIfNotExists.html#variant.Header
    """

    allow_unsafe_rename: bool | None = None
    """Allows tables writes that may conflict with concurrent writers."""

    def str_dict(self) -> dict[str, str]:
        """Storage options as str dict."""
        return _to_str_dict(self.dict())


class GcsConfig(Config):
    """Storage configuration for Google Cloud Storage object store."""

    provider: Literal["gcs"] = "gcs"

    service_account: str | None = None
    """Path to the service account file"""

    service_account_key: str | None = None
    """The serialized service account key."""

    bucket: str | None = None
    """Bucket name"""

    application_credentials: str | None = None
    """Application credentials path"""

    def str_dict(self) -> dict[str, str]:
        """Storage options as str dict."""
        return _to_str_dict(self.dict())


class ClientConfig(Config):
    """Configuration for http client interacting with storage APIs."""

    allow_http: bool | None = None
    """Allow non-TLS, i.e. non-HTTPS connections"""

    allow_invalid_certificates: bool | None = None
    """Skip certificate validation on https connections.

    ## Warning

    You should think very carefully before using this method.
    If invalid certificates are trusted, any certificate for any site will be trusted for use.
    This includes expired certificates. This introduces significant vulnerabilities,
    and should only be used as a last resort or for testing
    """

    connect_timeout: int | None = None
    """Timeout for only the connect phase of a Client"""

    default_content_type: str | None = None
    """default CONTENT_TYPE for uploads"""

    http1_only: bool | None = None
    """Only use http1 connections"""

    http2_keep_alive_interval: int | None = None
    """Interval for HTTP2 Ping frames should be sent to keep a connection alive."""

    http2_keep_alive_timeout: int | None = None
    """Timeout for receiving an acknowledgement of the keep-alive ping."""

    http2_keep_alive_while_idle: int | None = None
    """Enable HTTP2 keep alive pings for idle connections"""

    http2_only: bool | None = None
    """Only use http2 connections"""

    pool_idle_timeout: int | None = None
    """The pool max idle timeout

    This is the length of time an idle connection will be kept alive
    """

    pool_max_idle_per_host: int | None = None
    """maximum number of idle connections per host"""

    proxy_url: str | None = None
    """HTTP proxy to use for requests"""

    timeout: str | None = None
    """Request timeout (e.g. "120s")

    The timeout is applied from when the request starts connecting until the response body has finished
    """

    user_agent: str | None = None
    """User-Agent header to be used by this client"""

    def str_dict(self) -> dict[str, str]:
        """Storage options as str dict."""
        return _to_str_dict(self.dict())
