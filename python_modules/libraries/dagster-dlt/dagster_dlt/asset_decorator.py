from collections.abc import Mapping, Sequence
from typing import Any, Callable, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    BackfillPolicy,
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
    _check as check,
    multi_asset,
)
from dlt.extract.source import DltSource
from dlt.pipeline.pipeline import Pipeline

from dagster_dlt.constants import META_KEY_PIPELINE, META_KEY_SOURCE, META_KEY_TRANSLATOR
from dagster_dlt.translator import DagsterDltTranslator, DltResourceTranslatorData


def build_dlt_asset_specs(
    dlt_source: DltSource,
    dlt_pipeline: Pipeline,
    dagster_dlt_translator: Optional[DagsterDltTranslator] = None,
) -> Sequence[AssetSpec]:
    """Build a list of asset specs from a dlt source and pipeline.

    Args:
        dlt_source (DltSource): dlt source object
        dlt_pipeline (Pipeline): dlt pipeline object
        dagster_dlt_translator (Optional[DagsterDltTranslator]): Allows customizing how to
            map dlt project to asset keys and asset metadata.

    Returns:
        List[AssetSpec] list of asset specs from dlt source and pipeline

    """
    dagster_dlt_translator = dagster_dlt_translator or DagsterDltTranslator()
    return [
        dagster_dlt_translator.get_asset_spec(
            DltResourceTranslatorData(
                resource=dlt_source_resource, destination=dlt_pipeline.destination
            )
        ).merge_attributes(
            metadata={
                META_KEY_SOURCE: dlt_source,
                META_KEY_PIPELINE: dlt_pipeline,
                META_KEY_TRANSLATOR: dagster_dlt_translator,
            }
        )
        for dlt_source_resource in dlt_source.selected_resources.values()
    ]


def dlt_assets(
    *,
    dlt_source: DltSource,
    dlt_pipeline: Pipeline,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_dlt_translator: Optional[DagsterDltTranslator] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    pool: Optional[str] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Asset Factory for using data load tool (dlt).

    Args:
        dlt_source (DltSource): The DltSource to be ingested.
        dlt_pipeline (Pipeline): The dlt Pipeline defining the destination parameters.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_dlt_translator (DagsterDltTranslator, optional): Customization object for defining asset parameters from dlt resources.
        partitions_def (Optional[PartitionsDefinition]): Optional partitions definition.
        backfill_policy (Optional[BackfillPolicy]): If a partitions_def is defined, this determines
            how to execute backfills that target multiple partitions. If a time window partition
            definition is used, this parameter defaults to a single-run policy.
        op_tags (Optional[Mapping[str, Any]]): The tags for the underlying op.
        pool (Optional[str]): A string that identifies the concurrency pool that governs the dlt assets' execution.

    Examples:
        Loading Hubspot data to Snowflake with an auto materialize policy using the dlt verified source:

        .. code-block:: python

            from dagster_dlt import DagsterDltResource, DagsterDltTranslator, dlt_assets


            class HubspotDagsterDltTranslator(DagsterDltTranslator):
                @public
                def get_auto_materialize_policy(self, resource: DltResource) -> Optional[AutoMaterializePolicy]:
                    return AutoMaterializePolicy.eager().with_rules(
                        AutoMaterializeRule.materialize_on_cron("0 0 * * *")
                    )


            @dlt_assets(
                dlt_source=hubspot(include_history=True),
                dlt_pipeline=pipeline(
                    pipeline_name="hubspot",
                    dataset_name="hubspot",
                    destination="snowflake",
                    progress="log",
                ),
                name="hubspot",
                group_name="hubspot",
                dagster_dlt_translator=HubspotDagsterDltTranslator(),
            )
            def hubspot_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
                yield from dlt.run(context=context)

        Loading Github issues to snowflake:

        .. code-block:: python

            from dagster_dlt import DagsterDltResource, dlt_assets


            @dlt_assets(
                dlt_source=github_reactions(
                    "dagster-io", "dagster", items_per_page=100, max_items=250
                ),
                dlt_pipeline=pipeline(
                    pipeline_name="github_issues",
                    dataset_name="github",
                    destination="snowflake",
                    progress="log",
                ),
                name="github",
                group_name="github",
            )
            def github_reactions_dagster_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
                yield from dlt.run(context=context)

    """
    dagster_dlt_translator = check.inst_param(
        dagster_dlt_translator or DagsterDltTranslator(),
        "dagster_dlt_translator",
        DagsterDltTranslator,
    )

    if (
        partitions_def
        and isinstance(partitions_def, TimeWindowPartitionsDefinition)
        and not backfill_policy
    ):
        backfill_policy = BackfillPolicy.single_run()

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        partitions_def=partitions_def,
        backfill_policy=backfill_policy,
        op_tags=op_tags,
        specs=build_dlt_asset_specs(
            dlt_source=dlt_source,
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=dagster_dlt_translator,
        ),
        pool=pool,
    )
