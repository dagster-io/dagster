from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union, cast

from dagster import (
    AssetKey,
    AssetSpec,
    _check as check,
)
from dagster._annotations import public
from dagster._record import record
from dagster._utils.log import get_dagster_logger
from looker_sdk.sdk.api40.methods import Looker40SDK
from looker_sdk.sdk.api40.models import Dashboard, DashboardFilter, LookmlModelExplore
from sqlglot.expressions import Table

from dagster_looker.lkml.dagster_looker_lkml_translator import build_deps_for_looker_view

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
    TABLE = "table"


@record
class LookmlView:
    view_name: str
    sql_table_name: Optional[str]
    local_file_path: Optional[Path]
    view_props: Optional[Mapping[str, Any]]


@record
class UpstreamTable:
    table: Table


@record
class LookerStructureData:
    structure_type: LookerStructureType
    data: Union[LookmlView, LookmlModelExplore, DashboardFilter, Dashboard, UpstreamTable]


class DagsterLookerApiTranslator:
    def get_view_asset_key(self, looker_structure: LookerStructureData) -> AssetKey:
        lookml_view = check.inst(looker_structure.data, LookmlView)
        return AssetKey(["view", lookml_view.view_name])

    def get_view_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
        view = check.inst(looker_structure.data, LookmlView)
        return AssetSpec(
            key=self.get_asset_key(looker_structure),
            kinds={
                "looker",
                "view",
            },
            deps=build_deps_for_looker_view(
                get_asset_key_for_view=lambda view: self.get_asset_key(
                    LookerStructureData(
                        structure_type=LookerStructureType.VIEW,
                        data=LookmlView(
                            view_name=view[2]["name"],
                            sql_table_name=view[2].get("sql_table_name") or view[2]["name"],
                            local_file_path=view[0],
                            view_props=view[2],
                        ),
                    )
                ),
                get_asset_key_for_table=lambda table: self.get_asset_key(
                    LookerStructureData(
                        structure_type=LookerStructureType.TABLE,
                        data=UpstreamTable(table=table[2]["table"]),
                    )
                ),
                lookml_structure=(view.local_file_path, "view", view.view_props),
            )
            if view.local_file_path and view.view_props
            else [],
        )

    def get_explore_asset_key(self, looker_structure: LookerStructureData) -> AssetKey:
        lookml_explore = check.inst(looker_structure.data, (LookmlModelExplore, DashboardFilter))
        if isinstance(lookml_explore, LookmlModelExplore):
            return AssetKey(check.not_none(lookml_explore.id))
        elif isinstance(lookml_explore, DashboardFilter):
            lookml_model_name = check.not_none(lookml_explore.model)
            lookml_explore_name = check.not_none(lookml_explore.explore)
            return AssetKey(f"{lookml_model_name}::{lookml_explore_name}")
        else:
            check.assert_never(lookml_explore)

    def get_explore_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
        lookml_explore = check.inst(looker_structure.data, (LookmlModelExplore, DashboardFilter))

        if isinstance(lookml_explore, LookmlModelExplore):
            explore_base_view = LookmlView(
                view_name=check.not_none(lookml_explore.view_name),
                sql_table_name=check.not_none(lookml_explore.sql_table_name),
                local_file_path=None,
                view_props=None,
            )

            explore_join_views = [
                LookmlView(
                    view_name=check.not_none(lookml_explore_join.from_ or lookml_explore_join.name),
                    sql_table_name=lookml_explore_join.sql_table_name,
                    local_file_path=None,
                    view_props=None,
                )
                for lookml_explore_join in (lookml_explore.joins or [])
            ]

            return AssetSpec(
                key=self.get_asset_key(looker_structure),
                deps=list(
                    {
                        self.get_view_asset_spec(
                            LookerStructureData(
                                structure_type=LookerStructureType.VIEW, data=lookml_view
                            )
                        ).key
                        for lookml_view in [explore_base_view, *explore_join_views]
                    }
                ),
                tags={
                    "dagster/kind/looker": "",
                    "dagster/kind/explore": "",
                },
            )
        elif isinstance(lookml_explore, DashboardFilter):
            return AssetSpec(key=self.get_asset_key(looker_structure))
        else:
            check.assert_never(lookml_explore)

    def get_dashboard_asset_key(self, looker_structure: LookerStructureData) -> AssetKey:
        looker_dashboard = check.inst(looker_structure.data, Dashboard)
        return AssetKey(f"{check.not_none(looker_dashboard.title)}_{looker_dashboard.id}")

    def get_dashboard_asset_spec(self, looker_structure: LookerStructureData) -> AssetSpec:
        looker_dashboard = check.inst(looker_structure.data, Dashboard)
        return AssetSpec(
            key=self.get_asset_key(looker_structure),
            deps=list(
                {
                    self.get_explore_asset_spec(
                        LookerStructureData(
                            structure_type=LookerStructureType.EXPLORE, data=dashboard_filter
                        )
                    ).key
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
            return self.get_view_asset_spec(looker_structure)
        if looker_structure.structure_type == LookerStructureType.EXPLORE:
            return self.get_explore_asset_spec(looker_structure)
        elif looker_structure.structure_type == LookerStructureType.DASHBOARD:
            return self.get_dashboard_asset_spec(looker_structure)
        else:
            check.assert_never(looker_structure.structure_type)

    @public
    def get_asset_key(self, looker_structure: LookerStructureData) -> AssetKey:
        if looker_structure.structure_type == LookerStructureType.VIEW:
            return self.get_view_asset_key(looker_structure)
        if looker_structure.structure_type == LookerStructureType.EXPLORE:
            return self.get_explore_asset_key(looker_structure)
        elif looker_structure.structure_type == LookerStructureType.DASHBOARD:
            return self.get_dashboard_asset_key(looker_structure)
        elif looker_structure.structure_type == LookerStructureType.TABLE:
            return AssetKey(
                [
                    part.name.replace("*", "_star")
                    for part in cast(UpstreamTable, looker_structure.data).table.parts
                ]
            )
        else:
            check.assert_never(looker_structure.structure_type)
