from typing import Iterable, Optional, Union

from dagster import (
    AssetKey,
    AssetSpec,
    MaterializeResult,
    _check as check,
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.result import AssetResult
from dlt.extract.resource import DltResource
from dlt.extract.source import DltSource
from dlt.pipeline.pipeline import Pipeline

from dagster_embedded_elt.dlt.translator import DagsterDltTranslator

from .computation import Computation, ComputationContext, Specs, SpecsArg
from .constants import META_KEY_PIPELINE, META_KEY_SOURCE, META_KEY_TRANSLATOR
from .resource import DagsterDltResource


def get_upstream_deps(resource: DltResource) -> Iterable[AssetKey]:
    if resource.is_transformer:
        pipe = resource._pipe  # noqa: SLF001
        while pipe.has_parent:
            pipe = pipe.parent
        return [AssetKey(f"{resource.source_name}_{pipe.name}")]
    return [AssetKey(f"{resource.source_name}_{resource.name}")]


def get_description(resource: DltResource) -> Optional[str]:
    pipe = resource._pipe  # noqa: SLF001
    # If the function underlying the resource is a single callable,
    # return the docstring of the callable.
    if len(pipe.steps) == 1 and callable(pipe.steps[0]):
        return pipe.steps[0].__doc__
    return None


class RunDlt(Computation):
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

            RunDlt(
                name="hubspot",
                dlt_source=hubspot(include_history=True),
                dlt_pipeline=pipeline(
                    pipeline_name="hubspot",
                    dataset_name="hubspot",
                    destination="snowflake",
                    progress="log",
                ),
                specs=RunDlt.default_specs().replace(
                    group_name="hubspot"
                    auto_materialize_policy=AutoMaterializePolicy.eager().with_rules(
                        AutoMaterializeRule.materialize_on_cron("0 0 * * *")
                    )
                ),
            )

        Loading Github issues to snowflake:

        .. code-block:: python

            RunDlt(
                name="github",
                dlt_source=github_reactions(
                    "dagster-io", "dagster", items_per_page=100, max_items=250
                ),
                dlt_pipeline=pipeline(
                    pipeline_name="github_issues",
                    dataset_name="github",
                    destination="snowflake",
                    progress="log",
                ),
                specs=RunDlt.default_specs().replace(group_name="github"),
            )
    """

    @classmethod
    def default_specs(cls, dlt_source: DltSource, dlt_pipeline: Pipeline) -> Specs:
        return Specs(
            [
                RunDlt.default_spec(dlt_source, dlt_pipeline, resource)
                for resource in dlt_source.selected_resources.values()
            ]
        )

    @classmethod
    def default_spec(
        cls, dlt_source: DltSource, dlt_pipeline: Pipeline, dlt_resource: DltResource
    ) -> AssetSpec:
        return AssetSpec(
            key=f"dlt_{dlt_resource.source_name}_{dlt_resource.name}",
            deps=get_upstream_deps(dlt_resource),
            description=get_description(dlt_resource),
            metadata={
                META_KEY_SOURCE: dlt_source,
                META_KEY_PIPELINE: dlt_pipeline,
                META_KEY_TRANSLATOR: None,
            },
            tags={
                "dagster/compute_kind": dlt_pipeline.destination.destination_name,
            },
        )

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        specs: Optional[SpecsArg] = None,
        dlt_source: DltSource,
        dlt_pipeline: Pipeline,
    ):
        self.dlt_source = dlt_source
        self.dlt_pipeline = dlt_pipeline
        super().__init__(name=name, specs=specs or self.default_specs(dlt_source, dlt_pipeline))

    def stream(self, context: ComputationContext) -> Iterable[Union[AssetResult, AssetCheckResult]]:
        dlt = DagsterDltResource()
        for result in dlt.run(
            context=context.to_asset_execution_context(),
            dlt_source=self.dlt_source,
            # provide dummy instance of this
            dagster_dlt_translator=DagsterDltTranslator(),
        ):
            yield check.inst(
                result,
                MaterializeResult,
                "Only MaterializeResult is supported since dlt is in an asset computation",
            )
