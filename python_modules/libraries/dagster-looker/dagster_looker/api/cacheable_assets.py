from typing import TYPE_CHECKING, Sequence

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    Failure,
    _check as check,
    external_assets_from_specs,
    multi_asset,
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
    LookmlView,
    RequestStartPdtBuild,
)

if TYPE_CHECKING:
    from dagster_looker.api.resource import LookerResource


class LookerCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        looker: "LookerResource",
        request_start_pdt_builds: Sequence[RequestStartPdtBuild],
        dagster_looker_translator: DagsterLookerApiTranslator,
    ):
        self._looker = looker
        self._request_start_pdt_builds = request_start_pdt_builds
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

        executable_pdt_assets = []
        for request_start_pdt_build in self._request_start_pdt_builds:

            @multi_asset(
                specs=[
                    self._dagster_looker_translator.get_asset_spec(
                        LookerStructureData(
                            structure_type=LookerStructureType.VIEW,
                            data=LookmlView(
                                view_name=request_start_pdt_build.view_name,
                                sql_table_name=None,
                            ),
                        )
                    )
                ],
                name=f"{request_start_pdt_build.model_name}_{request_start_pdt_build.view_name}",
                resource_defs={"looker": self._looker.get_resource_definition()},
            )
            def asset_fn(context: AssetExecutionContext):
                looker: "LookerResource" = context.resources.looker

                context.log.info(
                    f"Starting pdt build for Looker view `{request_start_pdt_build.view_name}` in Looker model `{request_start_pdt_build.model_name}`."
                )

                materialize_pdt = looker.get_sdk().start_pdt_build(
                    model_name=request_start_pdt_build.model_name,
                    view_name=request_start_pdt_build.view_name,
                    force_rebuild=request_start_pdt_build.force_rebuild,
                    force_full_incremental=request_start_pdt_build.force_full_incremental,
                    workspace=request_start_pdt_build.workspace,
                    source=f"Dagster run {context.run_id}" or request_start_pdt_build.source,
                )

                if not materialize_pdt.materialization_id:
                    raise Failure("No materialization id was returned from Looker API.")

                check_pdt = looker.get_sdk().check_pdt_build(
                    materialization_id=materialize_pdt.materialization_id
                )

                context.log.info(
                    f"Materialization id: {check_pdt.materialization_id}, "
                    f"response text: {check_pdt.resp_text}"
                )

            executable_pdt_assets.append(asset_fn)

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
            ),
            *executable_pdt_assets,
        ]
