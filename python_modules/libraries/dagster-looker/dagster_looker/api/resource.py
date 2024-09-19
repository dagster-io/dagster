from typing import TYPE_CHECKING, List, Sequence

from dagster import ConfigurableResource
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.cached_method import cached_method
from dagster._utils.log import get_dagster_logger
from looker_sdk import init40
from looker_sdk.rtl.api_settings import ApiSettings, SettingsConfig
from looker_sdk.sdk.api40.methods import Looker40SDK
from pydantic import Field

from dagster_looker.api.cacheable_assets import LookerCacheableAssetsDefinition
from dagster_looker.api.translator import LookerInstanceData

if TYPE_CHECKING:
    from looker_sdk.sdk.api40.models import LookmlModelExplore

logger = get_dagster_logger("dagster-looker")


class LookerResource(ConfigurableResource):
    """Represents a connection to a Looker instance and provides methods
    to interact with the Looker API.
    """

    base_url: str = Field(
        ...,
        description="Base URL for the Looker API. For example, https://your.cloud.looker.com.",
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

    def fetch_looker_data(self) -> LookerInstanceData:
        sdk = self.get_sdk()

        # Get explore names from models
        explores_for_model = {
            model.name: [explore.name for explore in (model.explores or []) if explore.name]
            for model in sdk.all_lookml_models()
            if model.name
        }

        # TODO: Fetch explores in parallel using asyncio
        explore_data: List["LookmlModelExplore"] = []
        for model_name, explore_names in explores_for_model.items():
            for explore_name in explore_names:
                try:
                    explore_data.append(sdk.lookml_model_explore(model_name, explore_name))
                except:
                    logger.warning(
                        f"Failed to fetch LookML explore '{explore_name}' for model '{model_name}'."
                    )

        # TODO: Get all the LookML views upstream of the explores
        return LookerInstanceData(
            explores_by_id={explore.id: explore for explore in explore_data if explore.id}
        )

    def build_assets(self) -> Sequence[CacheableAssetsDefinition]:
        return [LookerCacheableAssetsDefinition(self)]

    def build_defs(self) -> Definitions:
        return Definitions(assets=self.build_assets())
