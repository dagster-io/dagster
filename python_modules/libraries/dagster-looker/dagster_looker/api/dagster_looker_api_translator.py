from typing import Any, Dict, Mapping, Sequence, Union

from dagster import (
    AssetSpec,
    _check as check,
)
from dagster._record import record
from dagster._utils.log import get_dagster_logger
from looker_sdk.sdk.api40.methods import Looker40SDK
from looker_sdk.sdk.api40.models import Dashboard, DashboardFilter, LookmlModelExplore

logger = get_dagster_logger("dagster_looker")


@record
class LookerInstanceData:
    """A record representing all content in a Looker instance."""

    explores_by_id: Dict[str, LookmlModelExplore]
    dashboards_by_id: Dict[str, Dashboard]

    def to_cacheable_metadata(self, *, sdk: Looker40SDK) -> Mapping[str, Any]:
        return {
            "dashboards_by_id": {
                dashboard_id: (
                    sdk.serialize(api_model=dashboard_data).decode()  # type: ignore
                )
                for dashboard_id, dashboard_data in self.dashboards_by_id.items()
            },
            "explores_by_id": {
                explore_id: (
                    sdk.serialize(api_model=explore_data).decode()  # type: ignore
                )
                for explore_id, explore_data in self.explores_by_id.items()
            },
        }

    @staticmethod
    def from_cacheable_metadata(
        *, sdk: Looker40SDK, cacheable_metadata: Sequence[Mapping[str, Any]]
    ) -> "LookerInstanceData":
        explores_by_id = {
            explore_id: (
                sdk.deserialize(
                    data=serialized_lookml_explore,  # type: ignore
                    structure=LookmlModelExplore,
                )
            )
            for cached_metadata in cacheable_metadata
            for explore_id, serialized_lookml_explore in cached_metadata["explores_by_id"].items()
        }

        dashboards_by_id = {
            dashboard_id: (
                sdk.deserialize(
                    data=serialized_looker_dashboard,  # type: ignore
                    structure=Dashboard,
                )
            )
            for cached_metadata in cacheable_metadata
            for dashboard_id, serialized_looker_dashboard in cached_metadata[
                "dashboards_by_id"
            ].items()
        }

        return LookerInstanceData(
            explores_by_id=explores_by_id,
            dashboards_by_id=dashboards_by_id,
        )


class DagsterLookerApiTranslator:
    def get_explore_asset_spec(
        self, lookml_explore: Union[LookmlModelExplore, DashboardFilter]
    ) -> AssetSpec:
        if isinstance(lookml_explore, LookmlModelExplore):
            return AssetSpec(
                key=check.not_none(lookml_explore.id),
                tags={
                    "dagster/kind/looker": "",
                    "dagster/kind/explore": "",
                },
            )
        elif isinstance(lookml_explore, DashboardFilter):
            lookml_model_name = check.not_none(lookml_explore.model)
            lookml_explore_name = check.not_none(lookml_explore.explore)

            return AssetSpec(key=f"{lookml_model_name}::{lookml_explore_name}")

    def get_dashboard_asset_spec(self, looker_dashboard: Dashboard) -> AssetSpec:
        return AssetSpec(
            key=f"{check.not_none(looker_dashboard.title)}_{looker_dashboard.id}",
            deps=list(
                {
                    self.get_explore_asset_spec(dashboard_filter).key
                    for dashboard_filter in looker_dashboard.dashboard_filters or []
                }
            ),
            tags={
                "dagster/kind/looker": "",
                "dagster/kind/dashboard": "",
            },
        )

    def get_asset_spec(self, api_model: Union[LookmlModelExplore, Dashboard]) -> AssetSpec:
        if isinstance(api_model, Dashboard):
            return self.get_dashboard_asset_spec(api_model)
        elif isinstance(api_model, LookmlModelExplore):
            return self.get_explore_asset_spec(api_model)
