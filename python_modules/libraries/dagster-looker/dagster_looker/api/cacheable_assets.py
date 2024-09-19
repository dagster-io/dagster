from typing import TYPE_CHECKING, Sequence

from dagster import (
    AssetsDefinition,
    AssetSpec,
    _check as check,
    external_assets_from_specs,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from looker_sdk.sdk.api40.models import LookmlModelExplore

from dagster_looker.api.translator import LookerInstanceData

if TYPE_CHECKING:
    from dagster_looker.api.resource import LookerResource


class LookerCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(self, looker: "LookerResource"):
        self._looker = looker
        super().__init__(unique_id=self._looker.client_id)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        looker_instance_data = self._looker.fetch_looker_data()
        return [
            AssetsDefinitionCacheableData(
                extra_metadata={
                    explore_id: (
                        self._looker.get_sdk()
                        .serialize(api_model=explore_data)  # type: ignore
                        .decode()
                    )
                }
            )
            for explore_id, explore_data in looker_instance_data.explores_by_id.items()
        ]

    def build_definitions(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
    ) -> Sequence[AssetsDefinition]:
        a = LookerInstanceData(
            explores_by_id={
                explore_id: (
                    self._looker.get_sdk().deserialize(
                        data=explore_data,  # type: ignore
                        structure=LookmlModelExplore,
                    )
                )
                for entry in data
                for explore_id, explore_data in check.not_none(entry.extra_metadata).items()
            }
        )

        return [
            *external_assets_from_specs(
                [AssetSpec(key=explore_id) for explore_id, explore_data in a.explores_by_id.items()]
            )
        ]
