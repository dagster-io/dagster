from typing import Any, Callable, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    PartitionsDefinition,
    _check as check,
    multi_asset,
)
from dlt.extract.source import DltSource
from dlt.pipeline.pipeline import Pipeline

from .constants import META_KEY_PIPELINE, META_KEY_SOURCE, META_KEY_TRANSLATOR
from .translator import DagsterDltTranslator


def dlt_assets(
    *,
    dlt_source: DltSource,
    dlt_pipeline: Pipeline,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dlt_dagster_translator: Optional[DagsterDltTranslator] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Asset Factory for using data load tool (dlt).

    Args:
        dlt_source (DltSource): The DltSource to be ingested.
        dlt_pipeline (Pipeline): The dlt Pipeline defining the destination parameters.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dlt_dagster_translator (DltDagsterTranslator, optional): Customization object for defining asset parameters from dlt resources.

    Examples:
        Loading Hubspot data to Snowflake with an auto materialize policy using the dlt verified source:

        .. code-block:: python

            class HubspotDltDagsterTranslator(DltDagsterTranslator):
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
                dlt_dagster_translator=HubspotDltDagsterTranslator(),
            )
            def hubspot_assets(context: AssetExecutionContext, dlt: DltDagsterResource):
                yield from dlt.run(context=context)

        Loading Github issues to snowflake:

        .. code-block:: python

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
            def github_reactions_dagster_assets(context: AssetExecutionContext, dlt: DltDagsterResource):
                yield from dlt.run(context=context)

    """
    dlt_dagster_translator = (
        check.opt_inst_param(dlt_dagster_translator, "dlt_dagster_translator", DagsterDltTranslator)
        or DagsterDltTranslator()
    )
    destination_type = dlt_pipeline.destination.destination_name
    return multi_asset(
        name=name,
        group_name=group_name,
        compute_kind="dlt",
        can_subset=True,
        partitions_def=partitions_def,
        specs=[
            AssetSpec(
                key=dlt_dagster_translator.get_asset_key(dlt_source_resource),
                deps=dlt_dagster_translator.get_deps_asset_keys(dlt_source_resource),
                auto_materialize_policy=dlt_dagster_translator.get_auto_materialize_policy(
                    dlt_source_resource
                ),
                metadata={
                    META_KEY_SOURCE: dlt_source,
                    META_KEY_PIPELINE: dlt_pipeline,
                    META_KEY_TRANSLATOR: dlt_dagster_translator,
                    **dlt_dagster_translator.get_metadata(dlt_source_resource),
                },
                tags={"dagster/storage_kind": destination_type},
            )
            for dlt_source_resource in dlt_source.selected_resources.values()
        ],
    )
