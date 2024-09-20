from typing import TYPE_CHECKING, Dict, Optional, Sequence

from dagster import (
    ConfigurableResource,
    _check as check,
)
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.cached_method import cached_method
from dagster._utils.log import get_dagster_logger
from looker_sdk import init40
from looker_sdk.rtl.api_settings import ApiSettings, SettingsConfig
from looker_sdk.sdk.api40.methods import Looker40SDK
from pydantic import Field

from dagster_looker.api.cacheable_assets import LookerCacheableAssetsDefinition
from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerInstanceData,
)

if TYPE_CHECKING:
    from looker_sdk.sdk.api40.models import LookmlModelExplore


logger = get_dagster_logger("dagster_looker")


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

    def fetch_looker_instance_data(self) -> LookerInstanceData:
        """Fetches all explores and dashboards from the Looker instance.

        TODO: Fetch explores in parallel using asyncio
        TODO: Get all the LookML views upstream of the explores
        """
        sdk = self.get_sdk()

        # Get dashboards
        dashboards = sdk.all_dashboards()
        dashboards_by_id = {
            dashboard.id: sdk.dashboard(dashboard_id=dashboard.id)
            for dashboard in dashboards
            if dashboard.id and not dashboard.hidden
        }

        # Get explore names from models
        explores_for_model = {
            model.name: [explore.name for explore in (model.explores or []) if explore.name]
            for model in sdk.all_lookml_models()
            if model.name
        }

        explores_by_id: Dict[str, "LookmlModelExplore"] = {}
        for model_name, explore_names in explores_for_model.items():
            for explore_name in explore_names:
                try:
                    lookml_explore = sdk.lookml_model_explore(
                        lookml_model_name=model_name,
                        explore_name=explore_name,
                    )

                    explores_by_id[check.not_none(lookml_explore.id)] = lookml_explore
                except:
                    logger.warning(
                        f"Failed to fetch LookML explore '{explore_name}' for model '{model_name}'."
                    )

        return LookerInstanceData(
            explores_by_id=explores_by_id,
            dashboards_by_id=dashboards_by_id,
        )

    def build_assets(
        self,
        *,
        dagster_looker_translator: DagsterLookerApiTranslator,
    ) -> Sequence[CacheableAssetsDefinition]:
        dagster_looker_translator = check.inst(
            dagster_looker_translator, DagsterLookerApiTranslator
        )

        return [LookerCacheableAssetsDefinition(self, dagster_looker_translator)]

    def build_defs(
        self,
        *,
        dagster_looker_translator: Optional[DagsterLookerApiTranslator] = None,
    ) -> Definitions:
        dagster_looker_translator = check.inst(
            dagster_looker_translator or DagsterLookerApiTranslator(), DagsterLookerApiTranslator
        )

        return Definitions(
            assets=self.build_assets(dagster_looker_translator=dagster_looker_translator)
        )
