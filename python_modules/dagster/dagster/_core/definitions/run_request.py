from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Optional, Sequence, Set, Union, cast

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.events import AssetKey
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.definitions.unresolved_asset_job_definition import (
        UnresolvedAssetJobDefinition,
    )


@whitelist_for_serdes(old_storage_names={"JobType"})
class InstigatorType(Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"


@whitelist_for_serdes
class SkipReason(NamedTuple("_SkipReason", [("skip_message", PublicAttr[Optional[str]])])):
    """Represents a skipped evaluation, where no runs are requested. May contain a message to indicate
    why no runs were requested.

    Attributes:
        skip_message (Optional[str]): A message displayed in dagit for why this evaluation resulted
            in no requested runs.
    """

    def __new__(cls, skip_message: Optional[str] = None):
        return super(SkipReason, cls).__new__(
            cls,
            skip_message=check.opt_str_param(skip_message, "skip_message"),
        )


@whitelist_for_serdes
class AddDynamicPartitionsRequest(
    NamedTuple(
        "_AddDynamicPartitionsRequest",
        [
            ("partitions_def_name", str),
            ("partition_keys", Sequence[str]),
        ],
    )
):
    """A request to add partitions to a dynamic partitions definition, to be evaluated by a sensor or schedule.
    """

    def __new__(
        cls,
        partitions_def_name: str,
        partition_keys: Sequence[str],
    ):
        return super(AddDynamicPartitionsRequest, cls).__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
        )


@whitelist_for_serdes
class DeleteDynamicPartitionsRequest(
    NamedTuple(
        "_AddDynamicPartitionsRequest",
        [
            ("partitions_def_name", str),
            ("partition_keys", Sequence[str]),
        ],
    )
):
    """A request to delete partitions to a dynamic partitions definition, to be evaluated by a sensor or schedule.
    """

    def __new__(
        cls,
        partitions_def_name: str,
        partition_keys: Sequence[str],
    ):
        return super(DeleteDynamicPartitionsRequest, cls).__new__(
            cls,
            partitions_def_name=check.str_param(partitions_def_name, "partitions_def_name"),
            partition_keys=check.list_param(partition_keys, "partition_keys", of_type=str),
        )


@whitelist_for_serdes
class RunRequest(
    NamedTuple(
        "_RunRequest",
        [
            ("run_key", PublicAttr[Optional[str]]),
            ("run_config", PublicAttr[Mapping[str, Any]]),
            ("tags", PublicAttr[Mapping[str, str]]),
            ("job_name", PublicAttr[Optional[str]]),
            ("asset_selection", PublicAttr[Optional[Sequence[AssetKey]]]),
            ("stale_assets_only", PublicAttr[bool]),
            ("partition_key", PublicAttr[Optional[str]]),
        ],
    )
):
    """Represents all the information required to launch a single run.  Must be returned by a
    SensorDefinition or ScheduleDefinition's evaluation function for a run to be launched.

    Attributes:
        run_key (Optional[str]): A string key to identify this launched run. For sensors, ensures that
            only one run is created per run key across all sensor evaluations.  For schedules,
            ensures that one run is created per tick, across failure recoveries. Passing in a `None`
            value means that a run will always be launched per evaluation.
        run_config (Optional[Mapping[str, Any]]: Configuration for the run. If the job has
            a :py:class:`PartitionedConfig`, this value will override replace the config
            provided by it.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the launched run.
        job_name (Optional[str]): (Experimental) The name of the job this run request will launch.
            Required for sensors that target multiple jobs.
        asset_selection (Optional[Sequence[AssetKey]]): A sequence of AssetKeys that should be
            launched with this run.
        stale_assets_only (Optional[Sequence[AssetKey]]): Set to true to further narrow the asset
            selection to stale assets. If passed without an asset selection, all stale assets in the
            job will be materialized. If the job does not materialize assets, this flag is ignored.
        partition_key (Optional[str]): The partition key for this run request.
    """

    def __new__(
        cls,
        run_key: Optional[str] = None,
        run_config: Optional[Union["RunConfig", Mapping[str, Any]]] = None,
        tags: Optional[Mapping[str, str]] = None,
        job_name: Optional[str] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        stale_assets_only: bool = False,
        partition_key: Optional[str] = None,
    ):
        from dagster._core.definitions.run_config import convert_config_input

        return super(RunRequest, cls).__new__(
            cls,
            run_key=check.opt_str_param(run_key, "run_key"),
            run_config=check.opt_mapping_param(
                convert_config_input(run_config), "run_config", key_type=str
            ),
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
            job_name=check.opt_str_param(job_name, "job_name"),
            asset_selection=check.opt_nullable_sequence_param(
                asset_selection, "asset_selection", of_type=AssetKey
            ),
            stale_assets_only=check.bool_param(stale_assets_only, "stale_assets_only"),
            partition_key=check.opt_str_param(partition_key, "partition_key"),
        )

    def with_replaced_attrs(self, **kwargs: Any) -> "RunRequest":
        fields = self._asdict()
        for k in fields.keys():
            if k in kwargs:
                fields[k] = kwargs[k]
        return RunRequest(**fields)

    def with_resolved_tags_and_config(
        self,
        target_definition: Union["JobDefinition", "UnresolvedAssetJobDefinition"],
        dynamic_partitions_requests: Sequence[
            Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]
        ],
        current_time: Optional[datetime] = None,
        dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
    ) -> "RunRequest":
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.definitions.partition import (
            DynamicPartitionsDefinition,
            PartitionedConfig,
            PartitionsDefinition,
        )

        if self.partition_key is None:
            check.failed(
                "Cannot resolve partition for run request without partition key",
            )

        partitions_def = target_definition.partitions_def
        if partitions_def is None:
            check.failed(
                (
                    "Cannot resolve partition for run request when target job"
                    f" '{target_definition.name}' is unpartitioned."
                ),
            )
        partitions_def = cast(PartitionsDefinition, partitions_def)

        partitioned_config = (
            target_definition.partitioned_config
            if isinstance(target_definition, JobDefinition)
            else PartitionedConfig.from_flexible_config(target_definition.config, partitions_def)
        )
        if partitioned_config is None:
            check.failed(
                "Cannot resolve partition for run request on unpartitioned job",
            )

        if isinstance(partitions_def, DynamicPartitionsDefinition) and partitions_def.name:
            if not dynamic_partitions_store:
                check.failed(
                    "Cannot resolve partition for run request on dynamic partitions without"
                    " dynamic_partitions_store"
                )

            add_partition_keys: Set[str] = set()
            delete_partition_keys: Set[str] = set()
            for req in dynamic_partitions_requests:
                if isinstance(req, AddDynamicPartitionsRequest):
                    if req.partitions_def_name == partitions_def.name:
                        add_partition_keys.update(set(req.partition_keys))
                elif isinstance(req, DeleteDynamicPartitionsRequest):
                    if req.partitions_def_name == partitions_def.name:
                        delete_partition_keys.update(set(req.partition_keys))

            partition_keys_after_requests_resolved = (
                set(
                    dynamic_partitions_store.get_dynamic_partitions(
                        partitions_def_name=partitions_def.name
                    )
                )
                | add_partition_keys
            ) - delete_partition_keys

            if self.partition_key not in partition_keys_after_requests_resolved:
                check.failed(
                    f"Dynamic partition key {self.partition_key} for partitions def"
                    f" '{partitions_def.name}' is invalid. After dynamic partitions requests are"
                    " applied, it does not exist in the set of valid partition keys."
                )

        else:
            partitions_def.validate_partition_key(
                self.partition_key,
                dynamic_partitions_store=dynamic_partitions_store,
                current_time=current_time,
            )

        tags = {
            **(self.tags or {}),
            **partitioned_config.get_tags_for_partition_key(
                self.partition_key,
                job_name=target_definition.name,
            ),
        }

        return self.with_replaced_attrs(
            run_config=self.run_config
            if self.run_config
            else partitioned_config.get_run_config_for_partition_key(self.partition_key),
            tags=tags,
        )

    def has_resolved_partition(self) -> bool:
        # Backcompat run requests yielded via `run_request_for_partition` already have resolved
        # partitioning
        return self.tags.get(PARTITION_NAME_TAG) is not None if self.partition_key else True


@whitelist_for_serdes(
    storage_name="PipelineRunReaction",
    storage_field_names={
        "dagster_run": "pipeline_run",
    },
)
class DagsterRunReaction(
    NamedTuple(
        "_DagsterRunReaction",
        [
            ("dagster_run", Optional[DagsterRun]),
            ("error", Optional[SerializableErrorInfo]),
            ("run_status", Optional[DagsterRunStatus]),
        ],
    )
):
    """Represents a request that reacts to an existing dagster run. If success, it will report logs
    back to the run.

    Attributes:
        dagster_run (Optional[DagsterRun]): The dagster run that originates this reaction.
        error (Optional[SerializableErrorInfo]): user code execution error.
        run_status: (Optional[DagsterRunStatus]): The run status that triggered the reaction.
    """

    def __new__(
        cls,
        dagster_run: Optional[DagsterRun],
        error: Optional[SerializableErrorInfo] = None,
        run_status: Optional[DagsterRunStatus] = None,
    ):
        return super(DagsterRunReaction, cls).__new__(
            cls,
            dagster_run=check.opt_inst_param(dagster_run, "dagster_run", DagsterRun),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            run_status=check.opt_inst_param(run_status, "run_status", DagsterRunStatus),
        )


@experimental
class SensorResult(
    NamedTuple(
        "_SensorResult",
        [
            ("run_requests", Optional[Sequence[RunRequest]]),
            ("skip_reason", Optional[SkipReason]),
            ("cursor", Optional[str]),
            (
                "dynamic_partitions_requests",
                Optional[
                    Sequence[Union[DeleteDynamicPartitionsRequest, AddDynamicPartitionsRequest]]
                ],
            ),
        ],
    )
):
    """The result of a sensor evaluation.

    Attributes:
        run_requests (Optional[Sequence[RunRequest]]): A list
            of run requests to be executed.
        skip_reason (Optional[SkipReason]): A skip message indicating why sensor evaluation was skipped.
        cursor (Optional[str]): The cursor value for this sensor, which will be provided on the
            context for the next sensor evaluation.
        dynamic_partitions_requests (Optional[Sequence[Union[DeleteDynamicPartitionsRequest,
            AddDynamicPartitionsRequest]]]): A list of dynamic partition requests to request dynamic
            partition addition and deletion. Run requests will be evaluated using the state of the
            partitions with these changes applied.
    """

    def __new__(
        cls,
        run_requests: Optional[Sequence[RunRequest]] = None,
        skip_reason: Optional[SkipReason] = None,
        cursor: Optional[str] = None,
        dynamic_partitions_requests: Optional[
            Sequence[Union[DeleteDynamicPartitionsRequest, AddDynamicPartitionsRequest]]
        ] = None,
    ):
        if skip_reason and len(run_requests if run_requests else []) > 0:
            check.failed(
                "Expected a single SkipReason or one or more RunRequests: received both "
                "RunRequest and SkipReason"
            )

        return super(SensorResult, cls).__new__(
            cls,
            run_requests=check.opt_sequence_param(run_requests, "run_requests", RunRequest),
            skip_reason=check.opt_inst_param(skip_reason, "skip_reason", SkipReason),
            cursor=check.opt_str_param(cursor, "cursor"),
            dynamic_partitions_requests=check.opt_sequence_param(
                dynamic_partitions_requests,
                "dynamic_partitions_requests",
                (AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest),
            ),
        )
