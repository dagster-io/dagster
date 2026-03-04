"""Spark Declarative Pipeline Dagster component (state-backed, resolvable).

SparkDeclarativePipelineComponent discovers datasets via spark-pipelines dry-run (or
source_only), persists SparkPipelineState with Dagster serdes, and builds a multi_asset
that runs spark-pipelines run and yields MaterializeResults.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal, Optional

import dagster as dg
from dagster import AssetKey, AssetSpec, Definitions, deserialize_value, serialize_value
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)

from dagster_spark.components.spark_declarative_pipeline.discovery import (
    DiscoveredDataset,
    DiscoveryMode,
    SparkPipelineState,
    discover_datasets_fn,
)
from dagster_spark.components.spark_declarative_pipeline.resource import SparkPipelinesResource
from dagster_spark.components.spark_declarative_pipeline.scaffolder import (
    SparkDeclarativePipelineScaffolder,
)

ExecutionMode = Literal["incremental", "full_refresh"]


def _resolve_spark_pipelines_resource(_context: Any, value: Any) -> SparkPipelinesResource:
    """Resolve YAML/config to SparkPipelinesResource. Used by Resolver for spark_pipelines field."""
    if isinstance(value, SparkPipelinesResource):
        return value
    if value is None:
        return SparkPipelinesResource()
    return SparkPipelinesResource(**value) if isinstance(value, dict) else SparkPipelinesResource()


@scaffold_with(SparkDeclarativePipelineScaffolder)
@dataclass
class SparkDeclarativePipelineComponent(StateBackedComponent, dg.Resolvable):
    """State-backed component for Spark Declarative Pipelines (SDP).

    Discovers datasets via spark-pipelines dry-run (or source_only), caches state,
    and builds a multi_asset that runs spark-pipelines run and yields MaterializeResults.
    """

    pipeline_spec_path: str
    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.local_filesystem
    )
    spark_pipelines: Annotated[
        SparkPipelinesResource,
        Resolver(_resolve_spark_pipelines_resource),
    ] = field(default_factory=SparkPipelinesResource)
    op: Optional[OpSpec] = None
    execution_mode: ExecutionMode = "incremental"
    discovery_mode: DiscoveryMode = "dry_run_only"
    asset_attributes_by_dataset: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def defs_state_config(self) -> DefsStateConfig:
        """Resolved DefsStateConfig for where to read/write component state."""
        return DefsStateConfig.from_args(
            self.defs_state,
            default_key=f"SparkDeclarativePipelineComponent[{self.pipeline_spec_path}]",
        )

    def write_state_to_path(self, state_path: Path) -> None:
        """Run discovery and write SparkPipelineState (datasets) to state_path using Dagster serdes.

        Args:
            state_path: File path to write serialized state (parent used as working_dir for dry-run).
        """
        working_dir = state_path.parent
        resource = self.spark_pipelines
        datasets = discover_datasets_fn(
            pipeline_spec_path=self.pipeline_spec_path,
            discovery_mode=self.discovery_mode,
            working_dir=working_dir,
            spark_pipelines_cmd=resource.spark_pipelines_cmd,
            dry_run_extra_args=resource.dry_run_extra_args,
        )
        state = SparkPipelineState(
            datasets=datasets,
            pipeline_spec_path=self.pipeline_spec_path,
        )
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(serialize_value(state))

    def get_asset_spec(self, dataset: DiscoveredDataset) -> AssetSpec:
        """Build an AssetSpec for a discovered dataset. Override to customize key/metadata/group.

        Args:
            dataset: Discovered dataset from state.

        Returns:
            AssetSpec with key from dataset.name (split by '.' for multi-segment), optional deps
            from attributes (dependencies, upstream_dataset_names, or deps), and optional
            description/metadata/group/tags from asset_attributes_by_dataset.
        """
        attrs = self.asset_attributes_by_dataset.get(dataset.name, {})
        source_attrs = dataset.attributes or {}
        dep_names = (
            source_attrs.get("dependencies")
            or source_attrs.get("upstream_dataset_names")
            or source_attrs.get("deps")
            or []
        )
        if isinstance(dep_names, str):
            dep_names = [dep_names]
        deps = [AssetKey(d.split(".")) for d in dep_names] if dep_names else []
        return AssetSpec(
            key=dataset.name.split("."),
            deps=deps,
            description=attrs.get("description")
            or f"Spark Declarative Pipeline dataset: {dataset.name}",
            metadata=attrs.get("metadata"),
            group_name=attrs.get("group_name"),
            tags=attrs.get("tags"),
        )

    def build_defs_from_state(
        self,
        context: ComponentLoadContext,
        state_path: Optional[Path],
    ) -> Definitions:
        """Build Definitions with a multi_asset that runs spark_pipelines.run_and_observe.

        Deserializes SparkPipelineState from state_path, filters out temporary_view datasets
        unless listed in asset_attributes_by_dataset, and builds one multi_asset with
        can_subset=True that yields MaterializeResults via run_and_observe.

        Args:
            context: Component load context (path, etc.).
            state_path: Path to serialized state file; if None or missing, returns empty Definitions.

        Returns:
            Definitions containing the multi_asset and spark_pipelines resource.
        """
        if state_path is None or not state_path.exists():
            return Definitions()

        state = deserialize_value(state_path.read_text(), SparkPipelineState)
        datasets = state.datasets

        # Filter out temporary_view datasets unless explicitly overridden in asset_attributes_by_dataset
        def include_dataset(ds: DiscoveredDataset) -> bool:
            if ds.name in self.asset_attributes_by_dataset:
                return True
            dataset_type = (ds.attributes or {}).get("dataset_type") if ds.attributes else None
            if dataset_type == "temporary_view":
                return False
            return True

        datasets = [ds for ds in datasets if include_dataset(ds)]
        if not datasets:
            return Definitions()

        asset_specs = [self.get_asset_spec(ds) for ds in datasets]
        op_spec = self.op or OpSpec()
        pipeline_spec_path = state.pipeline_spec_path
        # Resolve path relative to component path
        if not Path(pipeline_spec_path).is_absolute():
            resolved_spec_path = (context.path / pipeline_spec_path).resolve()
        else:
            resolved_spec_path = Path(pipeline_spec_path)
        working_dir = context.path
        execution_mode = self.execution_mode

        @dg.multi_asset(
            specs=asset_specs,
            can_subset=True,
            name=op_spec.name or "spark_declarative_pipeline",
            op_tags=op_spec.tags,
            backfill_policy=op_spec.backfill_policy,
            pool=op_spec.pool,
        )
        def _spark_pipeline_asset(
            context: dg.AssetExecutionContext,
            spark_pipelines: SparkPipelinesResource,
        ) -> Any:
            keys = (
                list(context.selected_asset_keys)
                if context.selected_asset_keys
                else [s.key for s in asset_specs]
            )
            yield from spark_pipelines.run_and_observe(
                context=context,
                pipeline_spec_path=resolved_spec_path,
                working_dir=working_dir,
                execution_mode=execution_mode,
                asset_keys=keys,
            )

        return Definitions(
            assets=[_spark_pipeline_asset],
            resources={"spark_pipelines": self.spark_pipelines},
        )
