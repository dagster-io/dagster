from typing import TYPE_CHECKING, Sequence

from dagster import (
    AssetsDefinition,
    _check as check,
    external_assets_from_specs,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from looker_sdk.sdk.api40.models import Dashboard, LookmlModelExplore

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerInstanceData,
)

if TYPE_CHECKING:
    from dagster_looker.api.resource import LookerResource


class LookerCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        looker: "LookerResource",
        dagster_looker_translator: DagsterLookerApiTranslator,
    ):
        self._looker = looker
        self._dagster_looker_translator = dagster_looker_translator
        super().__init__(unique_id=self._looker.client_id)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        looker_instance_data = self._looker.fetch_looker_data()

        return [
            AssetsDefinitionCacheableData(
                extra_metadata={
                    "dashboards_by_id": {
                        dashboard_id: (
                            self._looker.get_sdk()
                            .serialize(api_model=dashboard_data)  # type: ignore
                            .decode()
                        )
                        for dashboard_id, dashboard_data in looker_instance_data.dashboards_by_id.items()
                    },
                    "explores_by_id": {
                        explore_id: (
                            self._looker.get_sdk()
                            .serialize(api_model=explore_data)  # type: ignore
                            .decode()
                        )
                        for explore_id, explore_data in looker_instance_data.explores_by_id.items()
                    },
                }
            )
        ]

    def build_definitions(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
    ) -> Sequence[AssetsDefinition]:
        cached_metadata_entries = [check.not_none(entry.extra_metadata) for entry in data]
        looker_instance_data = LookerInstanceData(
            explores_by_id={
                explore_id: (
                    self._looker.get_sdk().deserialize(
                        data=serialized_lookml_explore,  # type: ignore
                        structure=LookmlModelExplore,
                    )
                )
                for cached_metadata in cached_metadata_entries
                for explore_id, serialized_lookml_explore in cached_metadata[
                    "explores_by_id"
                ].items()
            },
            dashboards_by_id={
                dashboard_id: (
                    self._looker.get_sdk().deserialize(
                        data=serialized_looker_dashboard,  # type: ignore
                        structure=Dashboard,
                    )
                )
                for cached_metadata in cached_metadata_entries
                for dashboard_id, serialized_looker_dashboard in cached_metadata[
                    "dashboards_by_id"
                ].items()
            },
        )

        return [
            *external_assets_from_specs(
                [
                    *(
                        self._dagster_looker_translator.get_asset_spec(lookml_explore)
                        for lookml_explore in looker_instance_data.explores_by_id.values()
                    ),
                    *(
                        self._dagster_looker_translator.get_asset_spec(looker_dashboard)
                        for looker_dashboard in looker_instance_data.dashboards_by_id.values()
                    ),
                ]
            )
        ]
