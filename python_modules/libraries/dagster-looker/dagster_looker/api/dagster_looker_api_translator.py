from collections.abc import Mapping
from enum import Enum
from typing import Any, Optional, Union

from dagster import (
    AssetKey,
    AssetSpec,
    _check as check,
)
from dagster._annotations import deprecated, public
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._record import record
from dagster._utils.log import get_dagster_logger
from looker_sdk.sdk.api40.methods import Looker40SDK
from looker_sdk.sdk.api40.models import Dashboard, DashboardFilter, LookmlModelExplore, User

logger = get_dagster_logger("dagster_looker")


@record
class LookerInstanceData:
    """A record representing all content in a Looker instance."""

    explores_by_id: dict[str, LookmlModelExplore]
    dashboards_by_id: dict[str, Dashboard]
    users_by_id: dict[str, User]

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
            "users_by_id": {
                user_id: (sdk.serialize(api_model=user_data).decode())  # type: ignore
                for user_id, user_data in self.users_by_id.items()
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

        users_by_id = {
            user_id: (sdk.deserialize(data=serialized_user, structure=User))  # type: ignore
            for user_id, serialized_user in state["users_by_id"].items()
        }

        return LookerInstanceData(
            explores_by_id=explores_by_id,
            dashboards_by_id=dashboards_by_id,
            users_by_id=users_by_id,
        )


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
    base_url: Optional[str] = None


@record
class LookerApiTranslatorStructureData:
    """A record representing a structure in Looker and the Looker instance data.
    Includes the structure's type and data as returned from the API.
    """

    structure_data: "LookerStructureData"
    instance_data: Optional["LookerInstanceData"]

    @property
    def structure_type(self) -> LookerStructureType:
        return self.structure_data.structure_type

    @property
    def data(self) -> Union[LookmlView, LookmlModelExplore, DashboardFilter, Dashboard]:
        return self.structure_data.data

    @property
    def base_url(self) -> Optional[str]:
        return self.structure_data.base_url


class DagsterLookerApiTranslator:
    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterLookerApiTranslator.get_asset_spec().key` instead",
    )
    def get_view_asset_key(self, looker_structure: LookerApiTranslatorStructureData) -> AssetKey:
        return self.get_asset_spec(looker_structure).key

    def get_view_asset_spec(self, looker_structure: LookerApiTranslatorStructureData) -> AssetSpec:
        lookml_view = check.inst(looker_structure.data, LookmlView)
        return AssetSpec(
            key=AssetKey(["view", lookml_view.view_name]),
        )

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterLookerApiTranslator.get_asset_spec().key` instead",
    )
    def get_explore_asset_key(self, looker_structure: LookerApiTranslatorStructureData) -> AssetKey:
        return self.get_explore_asset_spec(looker_structure).key

    def get_explore_asset_spec(
        self, looker_structure: LookerApiTranslatorStructureData
    ) -> AssetSpec:
        lookml_explore = check.inst(looker_structure.data, (LookmlModelExplore, DashboardFilter))

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
                key=AssetKey(check.not_none(lookml_explore.id)),
                deps=list(
                    {
                        self.get_asset_spec(
                            LookerApiTranslatorStructureData(
                                structure_data=LookerStructureData(
                                    structure_type=LookerStructureType.VIEW, data=lookml_view
                                ),
                                instance_data=looker_structure.instance_data,
                            )
                        ).key
                        for lookml_view in [explore_base_view, *explore_join_views]
                    }
                ),
                tags={
                    "dagster/kind/looker": "",
                    "dagster/kind/explore": "",
                },
                metadata={
                    "dagster-looker/web_url": MetadataValue.url(
                        f"{looker_structure.base_url}/explore/{check.not_none(lookml_explore.id).replace('::', '/')}"
                    ),
                },
            )
        elif isinstance(lookml_explore, DashboardFilter):
            lookml_model_name = check.not_none(lookml_explore.model)
            lookml_explore_name = check.not_none(lookml_explore.explore)
            return AssetSpec(key=AssetKey(f"{lookml_model_name}::{lookml_explore_name}"))
        else:
            check.assert_never(lookml_explore)

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterLookerApiTranslator.get_asset_spec().key` instead",
    )
    def get_dashboard_asset_key(
        self, looker_structure: LookerApiTranslatorStructureData
    ) -> AssetKey:
        return self.get_asset_spec(looker_structure).key

    def get_dashboard_asset_spec(
        self, looker_structure: LookerApiTranslatorStructureData
    ) -> AssetSpec:
        looker_dashboard = check.inst(looker_structure.data, Dashboard)

        user = None
        if looker_structure.instance_data and looker_dashboard.user_id:
            user = looker_structure.instance_data.users_by_id.get(looker_dashboard.user_id)

        return AssetSpec(
            key=AssetKey(f"{check.not_none(looker_dashboard.title)}_{looker_dashboard.id}"),
            deps=list(
                {
                    self.get_asset_spec(
                        LookerApiTranslatorStructureData(
                            structure_data=LookerStructureData(
                                structure_type=LookerStructureType.EXPLORE, data=dashboard_filter
                            ),
                            instance_data=looker_structure.instance_data,
                        )
                    ).key
                    for dashboard_filter in looker_dashboard.dashboard_filters or []
                }
            ),
            tags={
                "dagster/kind/looker": "",
                "dagster/kind/dashboard": "",
            },
            metadata={
                "dagster-looker/web_url": MetadataValue.url(
                    f"{looker_structure.base_url}{looker_dashboard.url}"
                ),
            },
            owners=[user.email] if user and user.email else None,
        )

    @public
    def get_asset_spec(self, looker_structure: LookerApiTranslatorStructureData) -> AssetSpec:
        if looker_structure.structure_type == LookerStructureType.VIEW:
            return self.get_view_asset_spec(looker_structure)
        if looker_structure.structure_type == LookerStructureType.EXPLORE:
            return self.get_explore_asset_spec(looker_structure)
        elif looker_structure.structure_type == LookerStructureType.DASHBOARD:
            return self.get_dashboard_asset_spec(looker_structure)
        else:
            check.assert_never(looker_structure.structure_type)

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterLookerApiTranslator.get_asset_spec().key` instead",
    )
    @public
    def get_asset_key(self, looker_structure: LookerApiTranslatorStructureData) -> AssetKey:
        return self.get_asset_spec(looker_structure).key
