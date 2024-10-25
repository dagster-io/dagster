from typing import Sequence, Type, cast

from dagster import AssetExecutionContext, AssetsDefinition, Failure, multi_asset

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerStructureData,
    LookerStructureType,
    LookmlView,
    PdtBuildDefinition,
)
from dagster_looker.api.resource import LookerResource


def build_looker_pdt_assets_definitions(
    resource_key: str,
    pdt_build_definitions: Sequence[PdtBuildDefinition],
    dagster_looker_translator: Type[DagsterLookerApiTranslator] = DagsterLookerApiTranslator,
) -> Sequence[AssetsDefinition]:
    """Returns the AssetsDefinitions of the executable assets for the given the list of PDT build definitions.

    Args:
        resource_key (str): The resource key to use for the Looker resource.
        pdt_build_definitions (Optional[Sequence[RequestStartPdtBuild]]): A list of PDTs
            for which the assets will be created. These PDTs will be built when materializing the assets.
            See https://developers.looker.com/api/explorer/4.0/types/DerivedTable/RequestStartPdtBuild?sdk=py
            for documentation on all available fields.
        dagster_looker_translator (Optional[DagsterLookerApiTranslator]): The translator to
            use to convert Looker structures into assets. Defaults to DagsterLookerApiTranslator.

    Returns:
        AssetsDefinition: The AssetsDefinitions of the executable assets for the given list of PDT build definitions.
    """
    translator = dagster_looker_translator()
    result = []
    for pdt_build_definition in pdt_build_definitions:

        @multi_asset(
            specs=[
                translator.get_asset_spec(
                    LookerStructureData(
                        structure_type=LookerStructureType.VIEW,
                        data=LookmlView(
                            view_name=pdt_build_definition.view_name,
                            sql_table_name=None,
                        ),
                    )
                )
            ],
            name=f"{pdt_build_definition.model_name}_{pdt_build_definition.view_name}",
            required_resource_keys={resource_key},
        )
        def pdts(context: AssetExecutionContext):
            looker = cast(LookerResource, getattr(context.resources, resource_key))

            context.log.info(
                f"Starting pdt build for Looker view `{pdt_build_definition.view_name}` "
                f"in Looker model `{pdt_build_definition.model_name}`."
            )

            materialize_pdt = looker.get_sdk().start_pdt_build(
                model_name=pdt_build_definition.model_name,
                view_name=pdt_build_definition.view_name,
                force_rebuild=pdt_build_definition.force_rebuild,
                force_full_incremental=pdt_build_definition.force_full_incremental,
                workspace=pdt_build_definition.workspace,
                source=f"Dagster run {context.run_id}"
                if context.run_id
                else pdt_build_definition.source,
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
