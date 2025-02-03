from typing import TYPE_CHECKING, Optional

from dagster import ConfigurableResource
from obstore.store import S3Store
from pydantic import Field

if TYPE_CHECKING:
    from obstore.store import RetryConfig, S3Config


class S3ObjectStore(ConfigurableResource):
    access_key_id: str = Field(description="S3 access key ID to use when creating the S3 Store.")
    secret_access_key: str = Field(
        description="S3 secret access key to use when creating the S3 Store."
    )
    region: Optional[str] = Field(
        default=None, description="Specifies a custom region for the S3 Store."
    )
    endpoint: Optional[str] = Field(
        default=None, description="Specifies a custom endpoint for the S3 Store."
    )
    allow_http: bool = Field(
        default=False, description="Whether to allow http connections. By default, https is used."
    )
    allow_invalid_certificates: bool = Field(
        default=False,
        description="Whether to allow invalid certificates. By default, valid certs are required.",
    )

    def create_store(
        self, bucket: str, timeout: str = "60s", retry_config: Optional["RetryConfig"] = None
    ) -> S3Store:
        """Creates an S3 object store."""
        config: S3Config = {
            "access_key_id": self.access_key_id,
            "secret_access_key": self.secret_access_key,
        }
        return S3Store.from_env(
            bucket=bucket,
            config=config,
            client_options={
                "timeout": timeout,
                "allow_http": self.allow_http,
                "allow_invalid_certificates": self.allow_invalid_certificates,
            },
            retry_config=retry_config,
        )
