import logging
from abc import abstractmethod
from typing import Optional

from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger
from dagster._utils.cached_method import cached_method
from looker_sdk import api_settings, init40, methods40, models40
from pydantic import Field, PrivateAttr


class LookerApiCredentials:
    client_id: str = Field(..., description="The Looker client ID.")
    client_secret: str = Field(..., description="The Looker client secret.")


class DagsterLookerApiSettings(api_settings.ApiSettings):
    def __init__(self, *args, **kwargs):
        self.client_id = kwargs.pop("client_id")
        self.client_secret = kwargs.pop("client_secret")
        self.base_url = kwargs.pop("base_url")
        super().__init__(*args, **kwargs)

    def read_config(self) -> api_settings.SettingsConfig:
        config = super().read_config()
        config["client_id"] = self.client_id
        config["client_secret"] = self.client_secret
        config["base_url"] = self.base_url
        return config


class LookerResource(ConfigurableResource):
    credentials: LookerApiCredentials = Field(
        description=("Looker API credentials."),
    )
    instance_name: str = Field(
        description=(
            "The instance name of your Looker API path, as described in "
            "https://cloud.google.com/looker/docs/admin-panel-platform-api#api_host_url."
        ),
    )
    port: Optional[int] = Field(
        description=(
            "The port used by your Looker API path, as described in "
            "https://cloud.google.com/looker/docs/admin-panel-platform-api#api_host_url."
        ),
    )

    _client: methods40.Looker40SDK = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._client = init40(
            config_settings=DagsterLookerApiSettings(
                client_id=self.credentials.client_id,
                client_secret=self.credentials.client_secret,
                base_url=self.api_base_url,
            )
        )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def api_base_url(self) -> str:
        api_base_url = f"https://{self.instance_name}.cloud.looker.com"
        if self.port:
            api_base_url += f":{self.port}"
        return api_base_url

    def start_pdt_materialization(self, model_name: str, view_name) -> models40.MaterializePDT:
        return self._client.start_pdt_build(model_name=model_name, view_name=view_name)

    def get_pdt_materialization_status(self, materialization_id: str) -> models40.MaterializePDT:
        return self._client.check_pdt_build(materialization_id=materialization_id)

    def cancel_pdt_materialization(self, materialization_id: str) -> models40.MaterializePDT:
        return self._client.stop_pdt_build(materialization_id=materialization_id)

    @property
    @abstractmethod
    def _should_forward_logs(self) -> bool:
        raise NotImplementedError()

    def sync_and_poll(self) -> None:
        raise NotImplementedError()
