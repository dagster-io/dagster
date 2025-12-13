from collections.abc import Sequence
from typing import Optional, Union, cast

from dagster import AssetExecutionContext, AssetsDefinition, DagsterLogManager, Failure, multi_asset
from dagster._annotations import beta
from dagster._utils.warnings import deprecation_warning

from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    LookerStructureData,
    LookerStructureType,
    LookmlView,
    RequestStartPdtBuild,
)
from dagster_looker.api.resource import LookerResource


def core_looker_pdt_execution(
    looker: LookerResource,
    request: RequestStartPdtBuild,
    log: DagsterLogManager,
    run_id: Optional[str],
) -> None:
    log.info(
        f"Starting pdt build for Looker view `{request.view_name}` "
        f"in Looker model `{request.model_name}`."
    )

    materialize_pdt = looker.get_sdk().start_pdt_build(
        model_name=request.model_name,
        view_name=request.view_name,
        force_rebuild=request.force_rebuild,
        force_full_incremental=request.force_full_incremental,
        workspace=request.workspace,
        source=f"Dagster run {run_id}" if run_id else request.source,
    )

    if not materialize_pdt.materialization_id:
        raise Failure("No materialization id was returned from Looker API.")

    check_pdt = looker.get_sdk().check_pdt_build(
        materialization_id=materialize_pdt.materialization_id
    )

    log.info(
        f"Materialization id: {check_pdt.materialization_id}, response text: {check_pdt.resp_text}"
    )


@beta
def build_looker_pdt_assets_definitions(
    resource_key: str,
    request_start_pdt_builds: Sequence[RequestStartPdtBuild],
    dagster_looker_translator: Optional[
        Union[DagsterLookerApiTranslator, type[DagsterLookerApiTranslator]]
    ] = None,
) -> Sequence[AssetsDefinition]:
    """Returns the AssetsDefinitions of the executable assets for the given the list of refreshable PDTs.

    Args:
        resource_key (str): The resource key to use for the Looker resource.
        request_start_pdt_builds (Optional[Sequence[RequestStartPdtBuild]]): A list of requests to start PDT builds.
            See https://developers.looker.com/api/explorer/4.0/types/DerivedTable/RequestStartPdtBuild?sdk=py
            for documentation on all available fields.
        dagster_looker_translator (Optional[Union[DagsterLookerApiTranslator, Type[DagsterLookerApiTranslator]]]):
            The translator to use to convert Looker structures into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterLookerApiTranslator`.

    Returns:
        AssetsDefinition: The AssetsDefinitions of the executable assets for the given the list of refreshable PDTs.
    """
    if isinstance(dagster_looker_translator, type):
        deprecation_warning(
            subject="Support of `dagster_looker_translator` as a Type[DagsterLookerApiTranslator]",
            breaking_version="1.10",
            additional_warn_text=(
                "Pass an instance of DagsterLookerApiTranslator or subclass to `dagster_looker_translator` instead."
            ),
        )
        dagster_looker_translator = dagster_looker_translator()

    translator = dagster_looker_translator or DagsterLookerApiTranslator()
    result = []
    for request_start_pdt_build in request_start_pdt_builds:
        for request in request_start_pdt_builds:
            spec = translator.get_asset_spec(
                LookerApiTranslatorStructureData(
                    structure_data=LookerStructureData(
                        structure_type=LookerStructureType.VIEW,
                        data=LookmlView(
                            view_name=request.view_name,
                            sql_table_name=None,
                        ),
                    ),
                    instance_data=None,
                )
            )

            @multi_asset(
                specs=[spec],
                name=f"{request.model_name}_{request.view_name}",
                required_resource_keys={resource_key},
            )
            def pdts(context: AssetExecutionContext):
                looker = cast("LookerResource", getattr(context.resources, resource_key))
                core_looker_pdt_execution(looker, request, context.log, context.run_id)

            result.append(pdts)

    return result
