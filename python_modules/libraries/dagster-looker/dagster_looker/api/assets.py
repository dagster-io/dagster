from pathlib import Path
from typing import Optional, Sequence, Type, cast

import lkml
from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    AssetSpec,
    Failure,
    _check as check,
    multi_asset,
)
from dagster._annotations import experimental

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerStructureData,
    LookerStructureType,
    LookmlView,
    RequestStartPdtBuild,
)
from dagster_looker.api.resource import LookerApiDefsLoader, LookerFilter, LookerResource
from dagster_looker.lkml.asset_utils import postprocess_loaded_structures


@experimental
def build_looker_pdt_assets_definitions(
    resource_key: str,
    request_start_pdt_builds: Sequence[RequestStartPdtBuild],
    dagster_looker_translator: Type[DagsterLookerApiTranslator] = DagsterLookerApiTranslator,
) -> Sequence[AssetsDefinition]:
    """Returns the AssetsDefinitions of the executable assets for the given the list of refreshable PDTs.

    Args:
        resource_key (str): The resource key to use for the Looker resource.
        request_start_pdt_builds (Optional[Sequence[RequestStartPdtBuild]]): A list of requests to start PDT builds.
            See https://developers.looker.com/api/explorer/4.0/types/DerivedTable/RequestStartPdtBuild?sdk=py
            for documentation on all available fields.
        dagster_looker_translator (Optional[DagsterLookerApiTranslator]): The translator to
            use to convert Looker structures into assets. Defaults to DagsterLookerApiTranslator.

    Returns:
        AssetsDefinition: The AssetsDefinitions of the executable assets for the given the list of refreshable PDTs.
    """
    translator = dagster_looker_translator()
    result = []
    for request_start_pdt_build in request_start_pdt_builds:

        @multi_asset(
            specs=[
                translator.get_asset_spec(
                    LookerStructureData(
                        structure_type=LookerStructureType.VIEW,
                        data=LookmlView(
                            view_name=request_start_pdt_build.view_name,
                            sql_table_name=None,
                            local_file_path=None,
                            view_props=None,
                        ),
                    )
                )
            ],
            name=f"{request_start_pdt_build.model_name}_{request_start_pdt_build.view_name}",
            required_resource_keys={resource_key},
        )
        def pdts(context: AssetExecutionContext):
            looker = cast(LookerResource, getattr(context.resources, resource_key))

            context.log.info(
                f"Starting pdt build for Looker view `{request_start_pdt_build.view_name}` "
                f"in Looker model `{request_start_pdt_build.model_name}`."
            )

            materialize_pdt = looker.get_sdk().start_pdt_build(
                model_name=request_start_pdt_build.model_name,
                view_name=request_start_pdt_build.view_name,
                force_rebuild=request_start_pdt_build.force_rebuild,
                force_full_incremental=request_start_pdt_build.force_full_incremental,
                workspace=request_start_pdt_build.workspace,
                source=f"Dagster run {context.run_id}"
                if context.run_id
                else request_start_pdt_build.source,
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

        result.append(pdts)

    return result


@experimental
def load_looker_asset_specs_from_instance(
    looker_resource: LookerResource,
    dagster_looker_translator: Type[DagsterLookerApiTranslator] = DagsterLookerApiTranslator,
    looker_filter: Optional[LookerFilter] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Looker structures.

    Args:
        looker_resource (LookerResource): The Looker resource to fetch assets from.
        dagster_looker_translator (Type[DagsterLookerApiTranslator]): The translator to use
            to convert Looker structures into AssetSpecs. Defaults to DagsterLookerApiTranslator.

    Returns:
        List[AssetSpec]: The set of AssetSpecs representing the Looker structures.
    """
    return check.is_list(
        LookerApiDefsLoader(
            looker_resource=looker_resource,
            translator_cls=dagster_looker_translator,
            looker_filter=looker_filter or LookerFilter(),
        )
        .build_defs()
        .assets,
        AssetSpec,
    )


@experimental
def load_looker_view_specs_from_project(
    project_dir: Path,
    dagster_looker_translator: Type[DagsterLookerApiTranslator] = DagsterLookerApiTranslator,
) -> Sequence[AssetSpec]:
    view_specs = []
    for lookml_view_path in project_dir.rglob("*.view.lkml"):
        for lookml_view_props in lkml.load(lookml_view_path.read_text()).get("views", []):
            lookml_view = (lookml_view_path, "view", lookml_view_props)
            view_specs.append(lookml_view)
    views_postprocessed = postprocess_loaded_structures(view_specs)

    view_objs = [
        LookmlView(
            view_name=view[2]["name"],
            sql_table_name=view[2].get("sql_table_name") or view[2]["name"],
            local_file_path=view[0],
            view_props=view[2],
        )
        for view in views_postprocessed
    ]
    translator_inst = dagster_looker_translator()

    return [
        translator_inst.get_asset_spec(
            LookerStructureData(
                structure_type=LookerStructureType.VIEW,
                data=view_obj,
            )
        )
        for view_obj in view_objs
    ]
