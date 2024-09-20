from typing import Dict, Union

from dagster import (
    AssetSpec,
    _check as check,
)
from dagster._record import record
from looker_sdk.sdk.api40.models import Dashboard, DashboardFilter, LookmlModelExplore


@record
class LookerInstanceData:
    """A record representing all content in a Looker instance."""

    explores_by_id: Dict[str, LookmlModelExplore]
    dashboards_by_id: Dict[str, Dashboard]


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
