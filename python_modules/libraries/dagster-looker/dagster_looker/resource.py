from dagster import ConfigurableResource
from dagster._utils.cached_method import cached_method
from looker_sdk import init40
from looker_sdk.rtl.api_settings import ApiSettings, SettingsConfig
from looker_sdk.sdk.api40.methods import Looker40SDK
from pydantic import Field


class LookerResource(ConfigurableResource):
    """Represents a connection to a Looker instance and provides methods
    to interact with the Looker API.
    """

    base_url: str = Field(
        ..., description="Base URL for the Looker API. For example, https://your.cloud.looker.com."
    )
    client_id: str = Field(..., description="Client ID for the Looker API.")
    client_secret: str = Field(..., description="Client secret for the Looker API.")

    @cached_method
    def get_sdk(self) -> Looker40SDK:
        class DagsterLookerApiSettings(ApiSettings):
            def read_config(_self) -> SettingsConfig:
                return {
                    **super().read_config(),
                    "base_url": self.base_url,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }

        return init40(config_settings=DagsterLookerApiSettings())
