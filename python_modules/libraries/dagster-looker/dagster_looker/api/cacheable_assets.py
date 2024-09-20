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

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerInstanceData,
    LookerStructureData,
    LookerStructureType,
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
        return [
            AssetsDefinitionCacheableData(
                extra_metadata=self._looker.fetch_looker_instance_data().to_cacheable_metadata(
                    sdk=self._looker.get_sdk()
                )
            )
        ]

    def build_definitions(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
    ) -> Sequence[AssetsDefinition]:
        looker_instance_data = LookerInstanceData.from_cacheable_metadata(
            sdk=self._looker.get_sdk(),
            cacheable_metadata=[check.not_none(cached_data.extra_metadata) for cached_data in data],
        )

        return [
            *external_assets_from_specs(
                [
                    *(
                        self._dagster_looker_translator.get_asset_spec(
                            LookerStructureData(
                                structure_type=LookerStructureType.EXPLORE, data=lookml_explore
                            )
                        )
                        for lookml_explore in looker_instance_data.explores_by_id.values()
                    ),
                    *(
                        self._dagster_looker_translator.get_asset_spec(
                            LookerStructureData(
                                structure_type=LookerStructureType.DASHBOARD, data=looker_dashboard
                            )
                        )
                        for looker_dashboard in looker_instance_data.dashboards_by_id.values()
                    ),
                ]
            )
        ]
