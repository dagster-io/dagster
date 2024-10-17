import re
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Union

from dagster import (
    AssetSpec,
    _check as check,
)
from dagster._annotations import public
from dagster._record import record
from dagster._utils.log import get_dagster_logger
from looker_sdk.sdk.api40.methods import Looker40SDK
from looker_sdk.sdk.api40.models import Dashboard, DashboardFilter, LookmlModelExplore


def _clean_asset_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


logger = get_dagster_logger("dagster_looker")


@record
class LookerInstanceData:
    """A record representing all content in a Looker instance."""

    explores_by_id: Dict[str, LookmlModelExplore]
    dashboards_by_id: Dict[str, Dashboard]

    def to_state(self, sdk: Looker40SDK) -> Mapping[str, Any]:
        return {
            "dashboards_by_id": {
                dashboard_id: (sdk.serialize(api_model=dashboard_data).decode())  # type: ignore
                for dashboard_id, dashboard_data in self.dashboards_by_id.items()
            },
            "explores_by_id": {
                explore_id: (sdk.serialize(api_model=explore_data).decode())  # type: ignore
                for explore_id, explore_data in self.explores_by_id.items()
            },
        }

    @staticmethod
    def from_state(sdk: Looker40SDK, state: Mapping[str, Any]) -> "LookerInstanceData":
        explores_by_id = {
            explore_id: (
                sdk.deserialize(data=serialized_lookml_explore, structure=LookmlModelExplore)  # type: ignore
            )
            for explore_id, serialized_lookml_explore in state["explores_by_id"].items()
        }

        dashboards_by_id = {
            dashboard_id: (sdk.deserialize(data=serialized_looker_dashboard, structure=Dashboard))  # type: ignore
            for dashboard_id, serialized_looker_dashboard in state["dashboards_by_id"].items()
        }

        return LookerInstanceData(explores_by_id=explores_by_id, dashboards_by_id=dashboards_by_id)


@record
class RequestStartPdtBuild:
    """A request to start a PDT build. See https://developers.looker.com/api/explorer/4.0/types/DerivedTable/RequestStartPdtBuild?sdk=py
    for documentation on all available fields.

    Args:
        model_name: The model of the PDT to start building.
        view_name: The view name of the PDT to start building.
        force_rebuild: Force rebuild of required dependent PDTs, even if they are already materialized.
        force_full_incremental: Force involved incremental PDTs to fully re-materialize.
        workspace: Workspace in which to materialize selected PDT ('dev' or default 'production').
        source: The source of this request.
    """

    model_name: str
    view_name: str
    force_rebuild: Optional[str] = None
    force_full_incremental: Optional[str] = None
    workspace: Optional[str] = None
    source: Optional[str] = None


class LookerStructureType(Enum):
    VIEW = "view"
    EXPLORE = "explore"
    DASHBOARD = "dashboard"


@record
class LookmlView:
    view_name: str
    sql_table_name: Optional[str]


@record
class LookerStructureData:
    structure_type: LookerStructureType
    data: Union[LookmlView, LookmlModelExplore, DashboardFilter, Dashboard]


class DagsterLookerApiTranslator:
    def get_view_asset_spec(self, lookml_view: LookmlView) -> AssetSpec:
        return AssetSpec(
            key=["view", _clean_asset_name(lookml_view.view_name)],
        )

    def get_explore_asset_spec(
        self, lookml_explore: Union[LookmlModelExplore, DashboardFilter]
    ) -> AssetSpec:
        if isinstance(lookml_explore, LookmlModelExplore):
            explore_base_view = LookmlView(
                view_name=check.not_none(lookml_explore.view_name),
                sql_table_name=check.not_none(lookml_explore.sql_table_name),
            )

            explore_join_views = [
                LookmlView(
                    view_name=check.not_none(lookml_explore_join.from_ or lookml_explore_join.name),
                    sql_table_name=lookml_explore_join.sql_table_name,
                )
                for lookml_explore_join in (lookml_explore.joins or [])
            ]

            return AssetSpec(
                key=_clean_asset_name(check.not_none(lookml_explore.id)),
                deps=list(
                    {
                        self.get_view_asset_spec(lookml_view).key
                        for lookml_view in [explore_base_view, *explore_join_views]
                    }
                ),
                tags={
                    "dagster/kind/looker": "",
                    "dagster/kind/explore": "",
                },
            )
        elif isinstance(lookml_explore, DashboardFilter):
            lookml_model_name = check.not_none(lookml_explore.model)
            lookml_explore_name = check.not_none(lookml_explore.explore)

            return AssetSpec(key=_clean_asset_name(f"{lookml_model_name}::{lookml_explore_name}"))

    def get_dashboard_asset_spec(self, looker_dashboard: Dashboard) -> AssetSpec:
        return AssetSpec(
            key=_clean_asset_name(
                f"{check.not_none(looker_dashboard.title)}_{looker_dashboard.id}"
            ),
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

    @public
    def get_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
        if looker_structure.structure_type == LookerStructureType.VIEW:
            data = check.inst(looker_structure.data, LookmlView)

            return self.get_view_asset_spec(data)
        if looker_structure.structure_type == LookerStructureType.EXPLORE:
            data = check.inst(looker_structure.data, (LookmlModelExplore, DashboardFilter))

            return self.get_explore_asset_spec(data)
        elif looker_structure.structure_type == LookerStructureType.DASHBOARD:
            data = check.inst(looker_structure.data, Dashboard)

            return self.get_dashboard_asset_spec(data)
        else:
            check.assert_never(looker_structure.structure_type)
