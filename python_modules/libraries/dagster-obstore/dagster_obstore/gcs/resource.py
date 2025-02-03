from typing import TYPE_CHECKING, Optional

from dagster import ConfigurableResource
from obstore.store import GCSStore
from pydantic import Field

if TYPE_CHECKING:
    from obstore.store import GCSConfig, RetryConfig


class GCSObjectStore(ConfigurableResource):
    service_account: str = Field(
        description="GCS service account to use when creating the GCS Store."
    )
    service_account_key: str = Field(
        description="GCS service account key to use when creating the GCS Store."
    )
    service_account_path: Optional[str] = Field(
        default=None, description="Path of service account key to authenticate, for the GCS Store."
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
    ) -> GCSStore:
        """Creates an GCS object store."""
        config: GCSConfig = {
            "service_account": self.service_account,
            "service_account_key": self.service_account_key,
        }
        if self.service_account_path:
            config["service_account_path"] = self.service_account_path

        return GCSStore.from_env(
            bucket=bucket,
            config=config,
            client_options={
                "timeout": timeout,
                "allow_http": self.allow_http,
                "allow_invalid_certificates": self.allow_invalid_certificates,
            },
            retry_config=retry_config,
        )
