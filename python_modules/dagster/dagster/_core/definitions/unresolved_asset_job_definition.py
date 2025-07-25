import warnings
from collections.abc import Mapping, Sequence
from datetime import datetime
from itertools import groupby
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, Union  # noqa: UP035

from dagster_shared.record import IHaveNew, record_custom, replace

import dagster._check as check
from dagster._annotations import deprecated, deprecated_param, public
from dagster._core.definitions import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.job.asset_job import build_asset_job, get_asset_graph_for_job
from dagster._core.definitions.backfill_policy import resolve_backfill_policy
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition import (
    DynamicPartitionsDefinition,
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partitioned_config import PartitionedConfig
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.run_request import RunRequest
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.instance import DynamicPartitionsStore
from dagster._utils.tags import normalize_tags

if TYPE_CHECKING:
    from dagster._core.definitions import JobDefinition
    from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
    from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
    from dagster._core.definitions.run_config import RunConfig


@record_custom
class UnresolvedAssetJobDefinition(IHaveNew):
    name: str
    selection: AssetSelection
    config: Optional[Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig"]]
    description: Optional[str]
    tags: Optional[Mapping[str, str]]
    run_tags: Optional[Mapping[str, str]]
    metadata: Optional[Mapping[str, Any]]
    partitions_def: Optional[PartitionsDefinition]
    executor_def: Optional[ExecutorDefinition]
    hooks: Optional[AbstractSet[HookDefinition]]
    op_retry_policy: Optional[RetryPolicy]

    def __new__(
        cls,
        name: str,
        selection: AssetSelection,
        config: Optional[
            Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig", "RunConfig"]
        ] = None,
        description: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        run_tags: Optional[Mapping[str, str]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        hooks: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
    ):
        from dagster._core.definitions.run_config import convert_config_input

        return super().__new__(
            cls,
            name=name,
            selection=selection,
            config=convert_config_input(config),
            description=description,
            tags=tags,
            # If `run_tags` is set, then we use it, otherwise `tags` acts as both definition tags and
            # run tags. This is for backcompat with old behavior prior to the introduction of
            # `run_tags`.
            run_tags=run_tags if run_tags else tags,
            metadata=metadata,
            partitions_def=partitions_def,
            executor_def=executor_def,
            hooks=hooks,
            op_retry_policy=op_retry_policy,
        )

    @deprecated(
        breaking_version="2.0.0",
        additional_warn_text="Directly instantiate `RunRequest(partition_key=...)` instead.",
    )
    def run_request_for_partition(
        self,
        partition_key: str,
        run_key: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> RunRequest:
        """Creates a RunRequest object for a run that processes the given partition.

        Args:
            partition_key: The key of the partition to request a run for.
            run_key (Optional[str]): A string key to identify this launched run. For sensors, ensures that
                only one run is created per run key across all sensor evaluations.  For schedules,
                ensures that one run is created per tick, across failure recoveries. Passing in a `None`
                value means that a run will always be launched per evaluation.
            tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
                to the launched run.
            run_config (Optional[Mapping[str, Any]]: Configuration for the run. If the job has
                a :py:class:`PartitionedConfig`, this value will override replace the config
                provided by it.
            current_time (Optional[datetime]): Used to determine which time-partitions exist.
                Defaults to now.
            dynamic_partitions_store (Optional[DynamicPartitionsStore]): The DynamicPartitionsStore
                object that is responsible for fetching dynamic partitions. Required when the
                partitions definition is a DynamicPartitionsDefinition with a name defined. Users
                can pass the DagsterInstance fetched via `context.instance` to this argument.

        Returns:
            RunRequest: an object that requests a run to process the given partition.
        """
        from dagster._core.definitions.partitions.partitioned_config import PartitionedConfig

        if not self.partitions_def:
            check.failed("Called run_request_for_partition on a non-partitioned job")

        partitioned_config = PartitionedConfig.from_flexible_config(
            self.config, self.partitions_def
        )

        if (
            isinstance(self.partitions_def, DynamicPartitionsDefinition)
            and self.partitions_def.name
        ):
            # Do not support using run_request_for_partition with dynamic partitions,
            # since this requires querying the instance once per run request for the
            # existent dynamic partitions
            check.failed(
                "run_request_for_partition is not supported for dynamic partitions. Instead, use"
                " RunRequest(partition_key=...)"
            )

        with partition_loading_context(current_time, dynamic_partitions_store) as ctx:
            self.partitions_def.validate_partition_key(partition_key, ctx)

        run_config = (
            run_config
            if run_config is not None
            else partitioned_config.get_run_config_for_partition_key(partition_key)
        )
        run_request_tags = {
            **(tags or {}),
            **partitioned_config.get_tags_for_partition_key(partition_key),
        }

        return RunRequest(
            job_name=self.name,
            run_key=run_key,
            run_config=run_config,
            tags=run_request_tags,
            asset_selection=asset_selection,
            partition_key=partition_key,
        )

    def resolve(
        self,
        asset_graph: "AssetGraph",
        default_executor_def: Optional[ExecutorDefinition] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    ) -> "JobDefinition":
        """Resolve this UnresolvedAssetJobDefinition into a JobDefinition."""
        try:
            job_asset_graph = get_asset_graph_for_job(asset_graph, self.selection)
        except DagsterInvalidDefinitionError as e:
            raise DagsterInvalidDefinitionError(
                f'Error resolving selection for asset job "{self.name}": {e}'
            ) from e

        # Require that all assets in the job have the same backfill policy
        executable_nodes = {job_asset_graph.get(k) for k in job_asset_graph.executable_asset_keys}
        nodes_by_backfill_policy = dict(
            groupby((n for n in executable_nodes if n.is_partitioned), lambda n: n.backfill_policy)
        )
        backfill_policy = resolve_backfill_policy(nodes_by_backfill_policy.keys())

        if len(nodes_by_backfill_policy) > 1:
            keys_by_backfill_policy = {
                bp: [n.key.to_user_string() for n in nodes]
                for bp, nodes in nodes_by_backfill_policy.items()
            }
            warnings.warn(
                f"Asset job {self.name} materializes assets with varying BackfillPolicies."
                f" Using backfill policy with minimum `max_partitions_per_run`: {backfill_policy}."
                f"\n\nFound multiple backfill policies:\n\n{keys_by_backfill_policy}"
            )

        # Error if a PartitionedConfig is defined and any target asset has a backfill policy that
        # materializes anything other than a single partition per run. This is because
        # PartitionedConfig is a function that maps single partition keys to run config, so it's
        # behavior is undefined for multiple-partition runs.
        if backfill_policy.max_partitions_per_run != 1 and isinstance(
            self.config, PartitionedConfig
        ):
            raise DagsterInvalidDefinitionError(
                f"Asset job {self.name} materializes an asset with a BackfillPolicy targeting multiple partitions per run,"
                "but a PartitionedConfig was provided. PartitionedConfigs are not supported for "
                "jobs with multi-partition-per-run backfill policies."
            )

        return build_asset_job(
            self.name,
            asset_graph=job_asset_graph,
            config=self.config,
            description=self.description,
            tags=self.tags,
            run_tags=self.run_tags,
            metadata=self.metadata,
            partitions_def=self.partitions_def,
            executor_def=self.executor_def or default_executor_def,
            hooks=self.hooks,
            op_retry_policy=self.op_retry_policy,
            resource_defs=resource_defs,
            allow_different_partitions_defs=False,
        )

    def with_metadata(
        self, metadata: Mapping[str, "RawMetadataValue"]
    ) -> "UnresolvedAssetJobDefinition":
        return replace(self, metadata=metadata)


@deprecated_param(
    param="partitions_def",
    breaking_version="2.0.0",
    additional_warn_text="Partitioning is inferred from the selected assets, so setting this is redundant.",
)
@public
def define_asset_job(
    name: str,
    selection: Optional["CoercibleToAssetSelection"] = None,
    config: Optional[
        Union[ConfigMapping, Mapping[str, Any], "PartitionedConfig", "RunConfig"]
    ] = None,
    description: Optional[str] = None,
    tags: Optional[Mapping[str, object]] = None,
    run_tags: Optional[Mapping[str, object]] = None,
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    executor_def: Optional[ExecutorDefinition] = None,
    hooks: Optional[AbstractSet[HookDefinition]] = None,
    op_retry_policy: Optional["RetryPolicy"] = None,
) -> UnresolvedAssetJobDefinition:
    """Creates a definition of a job which will either materialize a selection of assets or observe
    a selection of source assets. This will only be resolved to a JobDefinition once placed in a
    project.

    Args:
        name (str):
            The name for the job.
        selection (Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]):
            The assets that will be materialized or observed when the job is run.

            The selected assets must all be included in the assets that are passed to the assets
            argument of the Definitions object that this job is included on.

            The string "my_asset*" selects my_asset and all downstream assets within the code
            location. A list of strings represents the union of all assets selected by strings
            within the list.

            The selection will be resolved to a set of assets when the location is loaded. If the
            selection resolves to all source assets, the created job will perform source asset
            observations. If the selection resolves to all regular assets, the created job will
            materialize assets. If the selection resolves to a mixed set of source assets and
            regular assets, an error will be thrown.

        config:
            Describes how the Job is parameterized at runtime.

            If no value is provided, then the schema for the job's run config is a standard
            format based on its ops and resources.

            If a dictionary is provided, then it must conform to the standard config schema, and
            it will be used as the job's run config for the job whenever the job is executed.
            The values provided will be viewable and editable in the Dagster UI, so be
            careful with secrets.

            If a :py:class:`ConfigMapping` object is provided, then the schema for the job's run config is
            determined by the config mapping, and the ConfigMapping, which should return
            configuration in the standard format to configure the job.
        tags (Optional[Mapping[str, object]]): A set of key-value tags that annotate the job and can
            be used for searching and filtering in the UI. Values that are not already strings will
            be serialized as JSON. If `run_tags` is not set, then the content of `tags` will also be
            automatically appended to the tags of any runs of this job.
        run_tags (Optional[Mapping[str, object]]):
            A set of key-value tags that will be automatically attached to runs launched by this
            job. Values that are not already strings will be serialized as JSON. These tag values
            may be overwritten by tag values provided at invocation time. If `run_tags` is set, then
            `tags` are not automatically appended to the tags of any runs of this job.
        metadata (Optional[Mapping[str, RawMetadataValue]]): Arbitrary metadata about the job.
            Keys are displayed string labels, and values are one of the following: string, float,
            int, JSON-serializable dict, JSON-serializable list, and one of the data classes
            returned by a MetadataValue static method.
        description (Optional[str]):
            A description for the Job.
        executor_def (Optional[ExecutorDefinition]):
            How this Job will be executed. Defaults to :py:class:`multi_or_in_process_executor`,
            which can be switched between multi-process and in-process modes of execution. The
            default mode of execution is multi-process.
        hooks (Optional[AbstractSet[HookDefinition]]): A set of hooks to be attached to each asset in the job.
            These hooks define logic that runs in response to events such as success or failure
            during the execution of individual assets.
        op_retry_policy (Optional[RetryPolicy]): The default retry policy for all ops that compute assets in this job.
            Only used if retry policy is not defined on the asset definition.
        partitions_def (Optional[PartitionsDefinition]): (Deprecated)
            Defines the set of partitions for this job. Deprecated because partitioning is inferred
            from the selected assets, so setting this is redundant.


    Returns:
        UnresolvedAssetJobDefinition: The job, which can be placed inside a project.

    Examples:
        .. code-block:: python

            # A job that targets all assets in the project:
            @asset
            def asset1():
                ...

            Definitions(
                assets=[asset1],
                jobs=[define_asset_job("all_assets")],
            )

            # A job that targets a single asset
            @asset
            def asset1():
                ...

            Definitions(
                assets=[asset1],
                jobs=[define_asset_job("all_assets", selection=[asset1])],
            )

            # A job that targets all the assets in a group:
            Definitions(
                assets=assets,
                jobs=[define_asset_job("marketing_job", selection=AssetSelection.groups("marketing"))],
            )

            @observable_source_asset
            def source_asset():
                ...

            # A job that observes a source asset:
            Definitions(
                assets=assets,
                jobs=[define_asset_job("observation_job", selection=[source_asset])],
            )

            # Resources are supplied to the assets, not the job:
            @asset(required_resource_keys={"slack_client"})
            def asset1():
                ...

            Definitions(
                assets=[asset1],
                jobs=[define_asset_job("all_assets")],
                resources={"slack_client": prod_slack_client},
            )

    """
    from dagster._core.definitions import AssetSelection

    # convert string-based selections to AssetSelection objects
    if selection is None:
        resolved_selection = AssetSelection.all()
    else:
        resolved_selection = AssetSelection.from_coercible(selection)

    return UnresolvedAssetJobDefinition(
        name=name,
        selection=resolved_selection,
        config=config,
        description=description,
        tags=normalize_tags(tags),
        # Need to preserve None value
        run_tags=normalize_tags(run_tags) if run_tags is not None else None,
        metadata=metadata,
        partitions_def=partitions_def,
        executor_def=executor_def,
        hooks=hooks,
        op_retry_policy=op_retry_policy,
    )
