"""This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.data_version import (
    DATA_VERSION_TAG,
    SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD,
    extract_data_version_from_entry,
)
from dagster._core.definitions.dependency import OpNode
from dagster._core.definitions.events import AssetKey, AssetLineageInfo
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.job_base import IJob
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import (
    PartitionMapping,
    infer_partition_mapping,
)
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.resource_definition import ScopedResourcesBuilder
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    has_one_dimension_time_window_partitioning,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.io_manager import IOManager
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    PARTITION_NAME_TAG,
)
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.types.dagster_type import DagsterType

from .input import InputContext
from .output import OutputContext, get_output_context

if TYPE_CHECKING:
    from dagster._core.definitions.data_version import (
        DataVersion,
    )
    from dagster._core.definitions.dependency import NodeHandle
    from dagster._core.definitions.resource_definition import Resources
    from dagster._core.event_api import EventLogRecord
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.state import KnownExecutionState
    from dagster._core.instance import DagsterInstance

    from .hook import HookContext


def is_iterable(obj: Any) -> bool:
    try:
        iter(obj)
    except:
        return False
    return True


class IPlanContext(ABC):
    """Context interface to represent run information that does not require access to user code.

    The information available via this interface is accessible to the system throughout a run.
    """

    @property
    @abstractmethod
    def plan_data(self) -> "PlanData":
        raise NotImplementedError()

    @property
    def job(self) -> IJob:
        return self.plan_data.job

    @property
    def dagster_run(self) -> DagsterRun:
        return self.plan_data.dagster_run

    @property
    def run_id(self) -> str:
        return self.dagster_run.run_id

    @property
    def run_config(self) -> Mapping[str, object]:
        return self.dagster_run.run_config

    @property
    def job_name(self) -> str:
        return self.dagster_run.job_name

    @property
    def instance(self) -> "DagsterInstance":
        return self.plan_data.instance

    @property
    def raise_on_error(self) -> bool:
        return self.plan_data.raise_on_error

    @property
    def retry_mode(self) -> RetryMode:
        return self.plan_data.retry_mode

    @property
    def execution_plan(self) -> "ExecutionPlan":
        return self.plan_data.execution_plan

    @property
    @abstractmethod
    def output_capture(self) -> Optional[Mapping[StepOutputHandle, Any]]:
        raise NotImplementedError()

    @property
    def log(self) -> DagsterLogManager:
        raise NotImplementedError()

    @property
    def logging_tags(self) -> Mapping[str, str]:
        return self.log.logging_metadata.all_tags()

    @property
    def event_tags(self) -> Mapping[str, str]:
        return self.log.logging_metadata.event_tags()

    def has_tag(self, key: str) -> bool:
        check.str_param(key, "key")
        return key in self.dagster_run.tags

    def get_tag(self, key: str) -> Optional[str]:
        check.str_param(key, "key")
        return self.dagster_run.tags.get(key)

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self.dagster_run.tags


class PlanData(NamedTuple):
    """The data about a run that is available during both orchestration and execution.

    This object does not contain any information that requires access to user code, such as the
    pipeline definition and resources.
    """

    job: IJob
    dagster_run: DagsterRun
    instance: "DagsterInstance"
    execution_plan: "ExecutionPlan"
    raise_on_error: bool = False
    retry_mode: RetryMode = RetryMode.DISABLED


class ExecutionData(NamedTuple):
    """The data that is available to the system during execution.

    This object contains information that requires access to user code, such as the pipeline
    definition and resources.
    """

    scoped_resources_builder: ScopedResourcesBuilder
    resolved_run_config: ResolvedRunConfig
    job_def: JobDefinition


class IStepContext(IPlanContext):
    """Interface to represent data to be available during either step orchestration or execution."""

    @property
    @abstractmethod
    def step(self) -> ExecutionStep:
        raise NotImplementedError()

    @property
    @abstractmethod
    def node_handle(self) -> "NodeHandle":
        raise NotImplementedError()


class PlanOrchestrationContext(IPlanContext):
    """Context for the orchestration of a run.

    This context assumes inability to run user code directly.
    """

    def __init__(
        self,
        plan_data: PlanData,
        log_manager: DagsterLogManager,
        executor: Executor,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
        resume_from_failure: bool = False,
    ):
        self._plan_data = plan_data
        self._log_manager = log_manager
        self._executor = executor
        self._output_capture = output_capture
        self._resume_from_failure = resume_from_failure

    @property
    def plan_data(self) -> PlanData:
        return self._plan_data

    @property
    def reconstructable_job(self) -> ReconstructableJob:
        if not isinstance(self.job, ReconstructableJob):
            raise DagsterInvariantViolationError(
                "reconstructable_pipeline property must be a ReconstructableJob"
            )
        return self.job

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def output_capture(self) -> Optional[Dict[StepOutputHandle, Any]]:
        return self._output_capture

    def for_step(self, step: ExecutionStep) -> "IStepContext":
        return StepOrchestrationContext(
            plan_data=self.plan_data,
            log_manager=self._log_manager.with_tags(**step.logging_tags),
            executor=self.executor,
            step=step,
            output_capture=self.output_capture,
        )

    @property
    def resume_from_failure(self) -> bool:
        return self._resume_from_failure


class StepOrchestrationContext(PlanOrchestrationContext, IStepContext):
    """Context for the orchestration of a step.

    This context assumes inability to run user code directly. Thus, it does not include any resource
    information.
    """

    def __init__(
        self,
        plan_data: PlanData,
        log_manager: DagsterLogManager,
        executor: Executor,
        step: ExecutionStep,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        super(StepOrchestrationContext, self).__init__(
            plan_data, log_manager, executor, output_capture
        )
        self._step = step

    @property
    def step(self) -> ExecutionStep:
        return self._step

    @property
    def node_handle(self) -> "NodeHandle":
        return self.step.node_handle


class PlanExecutionContext(IPlanContext):
    """Context for the execution of a plan.

    This context assumes that user code can be run directly, and thus includes resource and
    information.
    """

    def __init__(
        self,
        plan_data: PlanData,
        execution_data: ExecutionData,
        log_manager: DagsterLogManager,
        output_capture: Optional[Dict[StepOutputHandle, Any]] = None,
    ):
        self._plan_data = plan_data
        self._execution_data = execution_data
        self._log_manager = log_manager
        self._output_capture = output_capture

    @property
    def plan_data(self) -> PlanData:
        return self._plan_data

    @property
    def output_capture(self) -> Optional[Dict[StepOutputHandle, Any]]:
        return self._output_capture

    def for_step(
        self,
        step: ExecutionStep,
        known_state: Optional["KnownExecutionState"] = None,
    ) -> IStepContext:
        return StepExecutionContext(
            plan_data=self.plan_data,
            execution_data=self._execution_data,
            log_manager=self._log_manager.with_tags(**step.logging_tags),
            step=step,
            output_capture=self.output_capture,
            known_state=known_state,
        )

    @property
    def job_def(self) -> JobDefinition:
        return self._execution_data.job_def

    @property
    def resolved_run_config(self) -> ResolvedRunConfig:
        return self._execution_data.resolved_run_config

    @property
    def scoped_resources_builder(self) -> ScopedResourcesBuilder:
        return self._execution_data.scoped_resources_builder

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        from dagster._core.definitions.job_definition import JobDefinition

        job_def = self._execution_data.job_def
        if not isinstance(job_def, JobDefinition):
            check.failed(
                "Can only call 'partitions_def', when using jobs, not legacy pipelines",
            )
        partitions_def = job_def.partitions_def
        return partitions_def

    @property
    def has_partitions(self) -> bool:
        tags = self._plan_data.dagster_run.tags
        return bool(
            PARTITION_NAME_TAG in tags
            or any([tag.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX) for tag in tags.keys()])
            or (
                tags.get(ASSET_PARTITION_RANGE_START_TAG)
                and tags.get(ASSET_PARTITION_RANGE_END_TAG)
            )
        )

    @property
    def partition_key(self) -> str:
        from dagster._core.definitions.multi_dimensional_partitions import (
            MultiPartitionsDefinition,
            get_multipartition_key_from_tags,
        )

        if not self.has_partitions:
            raise DagsterInvariantViolationError(
                "Cannot access partition_key for a non-partitioned run"
            )

        tags = self._plan_data.dagster_run.tags
        if any([tag.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX) for tag in tags.keys()]):
            return get_multipartition_key_from_tags(tags)
        elif PARTITION_NAME_TAG in tags:
            return tags[PARTITION_NAME_TAG]
        else:
            range_start = tags[ASSET_PARTITION_RANGE_START_TAG]
            range_end = tags[ASSET_PARTITION_RANGE_END_TAG]

            if range_start != range_end:
                raise DagsterInvariantViolationError(
                    "Cannot access partition_key for a partitioned run with a range of partitions."
                    " Call partition_key_range instead."
                )
            else:
                if isinstance(self.partitions_def, MultiPartitionsDefinition):
                    return self.partitions_def.get_partition_key_from_str(cast(str, range_start))
                return cast(str, range_start)

    @property
    def asset_partition_key_range(self) -> PartitionKeyRange:
        from dagster._core.definitions.multi_dimensional_partitions import (
            MultiPartitionsDefinition,
            get_multipartition_key_from_tags,
        )

        if not self.has_partitions:
            raise DagsterInvariantViolationError(
                "Cannot access partition_key for a non-partitioned run"
            )

        tags = self._plan_data.dagster_run.tags
        if any([tag.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX) for tag in tags.keys()]):
            multipartition_key = get_multipartition_key_from_tags(tags)
            return PartitionKeyRange(multipartition_key, multipartition_key)
        elif PARTITION_NAME_TAG in tags:
            partition_key = tags[PARTITION_NAME_TAG]
            return PartitionKeyRange(partition_key, partition_key)
        else:
            partition_key_range_start = tags[ASSET_PARTITION_RANGE_START_TAG]
            if partition_key_range_start is not None:
                if isinstance(self.partitions_def, MultiPartitionsDefinition):
                    return PartitionKeyRange(
                        self.partitions_def.get_partition_key_from_str(partition_key_range_start),
                        self.partitions_def.get_partition_key_from_str(
                            tags[ASSET_PARTITION_RANGE_END_TAG]
                        ),
                    )
            return PartitionKeyRange(partition_key_range_start, tags[ASSET_PARTITION_RANGE_END_TAG])

    @property
    def partition_time_window(self) -> TimeWindow:
        partitions_def = self.partitions_def

        if partitions_def is None:
            raise DagsterInvariantViolationError("Partitions definition is not defined")

        if not has_one_dimension_time_window_partitioning(partitions_def=partitions_def):
            raise DagsterInvariantViolationError(
                "Expected a TimeWindowPartitionsDefinition or MultiPartitionsDefinition with a"
                f" single time dimension, but instead found {type(partitions_def)}"
            )

        if self.has_partition_key:
            return cast(
                Union[MultiPartitionsDefinition, TimeWindowPartitionsDefinition], partitions_def
            ).time_window_for_partition_key(self.partition_key)
        elif self.has_partition_key_range:
            partition_key_range = self.asset_partition_key_range
            partitions_def = cast(
                Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition], partitions_def
            )
            return TimeWindow(
                partitions_def.time_window_for_partition_key(partition_key_range.start).start,
                partitions_def.time_window_for_partition_key(partition_key_range.end).end,
            )

        else:
            check.failed(
                "Has a PartitionsDefinition, so should either have a partition key or a partition"
                " key range"
            )

    @property
    def has_partition_key(self) -> bool:
        return PARTITION_NAME_TAG in self._plan_data.dagster_run.tags

    @property
    def has_partition_key_range(self) -> bool:
        return ASSET_PARTITION_RANGE_START_TAG in self._plan_data.dagster_run.tags

    def for_type(self, dagster_type: DagsterType) -> "TypeCheckContext":
        return TypeCheckContext(
            self.run_id, self.log, self._execution_data.scoped_resources_builder, dagster_type
        )


@dataclass
class InputAssetVersionInfo:
    # This is the storage id of the last materialization of any partition of an asset. Thus it is
    # computed the same way for both partitioned and non-partitioned assets.
    storage_id: int

    # If the input asset is partitioned, this is a hash of the sorted data versions of each dependency
    # partition. If the input asset is not partitioned, this is the data version of the asset. It
    # can be none if we are sourcing a materialization from before data versions.
    data_version: Optional["DataVersion"]

    # This is the run_id on the event that the storage_id references
    run_id: str

    # This is the timestamp on the event that the storage_id references
    timestamp: float


class StepExecutionContext(PlanExecutionContext, IStepContext):
    """Context for the execution of a step. Users should not instantiate this class directly.

    This context assumes that user code can be run directly, and thus includes resource and information.
    """

    def __init__(
        self,
        plan_data: PlanData,
        execution_data: ExecutionData,
        log_manager: DagsterLogManager,
        step: ExecutionStep,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
        known_state: Optional["KnownExecutionState"],
    ):
        from dagster._core.execution.resources_init import get_required_resource_keys_for_step

        super(StepExecutionContext, self).__init__(
            plan_data=plan_data,
            execution_data=execution_data,
            log_manager=log_manager,
            output_capture=output_capture,
        )
        self._step = step
        self._required_resource_keys = get_required_resource_keys_for_step(
            plan_data.job.get_definition(),
            step,
            plan_data.execution_plan,
        )
        self._resources = execution_data.scoped_resources_builder.build(
            self._required_resource_keys
        )
        self._known_state = known_state
        self._input_lineage: List[AssetLineageInfo] = []

        resources_iter = cast(Iterable, self._resources)

        step_launcher_resources = [
            resource for resource in resources_iter if isinstance(resource, StepLauncher)
        ]

        self._step_launcher: Optional[StepLauncher] = None
        if len(step_launcher_resources) > 1:
            raise DagsterInvariantViolationError(
                "Multiple required resources for {described_op} have inherited StepLauncher"
                "There should be at most one step launcher resource per {node_type}.".format(
                    described_op=self.describe_op(), node_type=self.op_def.node_type_str
                )
            )
        elif len(step_launcher_resources) == 1:
            self._step_launcher = step_launcher_resources[0]

        self._step_exception: Optional[BaseException] = None

        self._step_output_capture: Optional[Dict[StepOutputHandle, Any]] = None
        # Enable step output capture if there are any hooks which will receive them.
        # Expect in the future that hooks may control whether or not they get outputs,
        # but for now presence of any will cause output capture.
        if self.job_def.get_all_hooks_for_handle(self.node_handle):
            self._step_output_capture = {}

        self._output_metadata: Dict[str, Any] = {}
        self._seen_outputs: Dict[str, Union[str, Set[str]]] = {}

        self._input_asset_version_info: Dict[AssetKey, Optional["InputAssetVersionInfo"]] = {}
        self._is_external_input_asset_version_info_loaded = False
        self._data_version_cache: Dict[AssetKey, "DataVersion"] = {}

        self._requires_typed_event_stream = False
        self._typed_event_stream_error_message = None

    # In this mode no conversion is done on returned values and missing but expected outputs are not
    # allowed.
    @property
    def requires_typed_event_stream(self) -> bool:
        return self._requires_typed_event_stream

    @property
    def typed_event_stream_error_message(self) -> Optional[str]:
        return self._typed_event_stream_error_message

    # Error message will be appended to the default error message.
    def set_requires_typed_event_stream(self, *, error_message: Optional[str] = None):
        self._requires_typed_event_stream = True
        self._typed_event_stream_error_message = error_message

    @property
    def step(self) -> ExecutionStep:
        return self._step

    @property
    def node_handle(self) -> "NodeHandle":
        return self.step.node_handle

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return self._required_resource_keys

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        return self._step_launcher

    @property
    def op_def(self) -> OpDefinition:
        return self.op.definition

    @property
    def job_def(self) -> "JobDefinition":
        return self._execution_data.job_def

    @property
    def op(self) -> OpNode:
        return self.job_def.get_op(self._step.node_handle)

    @property
    def op_retry_policy(self) -> Optional[RetryPolicy]:
        return self.job_def.get_retry_policy_for_handle(self.node_handle)

    def describe_op(self) -> str:
        return f'op "{self.node_handle}"'

    def get_io_manager(self, step_output_handle: StepOutputHandle) -> IOManager:
        step_output = self.execution_plan.get_step_output(step_output_handle)
        io_manager_key = (
            self.job_def.get_node(step_output.node_handle)
            .output_def_named(step_output.name)
            .io_manager_key
        )

        output_manager = getattr(self.resources, io_manager_key)
        return check.inst(output_manager, IOManager)

    def get_output_context(self, step_output_handle: StepOutputHandle) -> OutputContext:
        return get_output_context(
            self.execution_plan,
            self.job_def,
            self.resolved_run_config,
            step_output_handle,
            self._get_source_run_id(step_output_handle),
            log_manager=self.log,
            step_context=self,
            resources=None,
            version=self.execution_plan.get_version_for_step_output_handle(step_output_handle),
        )

    def for_input_manager(
        self,
        name: str,
        config: Any,
        metadata: Any,
        dagster_type: DagsterType,
        source_handle: Optional[StepOutputHandle] = None,
        resource_config: Any = None,
        resources: Optional["Resources"] = None,
        artificial_output_context: Optional["OutputContext"] = None,
    ) -> InputContext:
        if source_handle and artificial_output_context:
            check.failed("Cannot specify both source_handle and artificial_output_context.")

        upstream_output: Optional[OutputContext] = None

        if source_handle is not None:
            version = self.execution_plan.get_version_for_step_output_handle(source_handle)

            # NOTE: this is using downstream step_context for upstream OutputContext. step_context
            # will be set to None for 0.15 release.
            upstream_output = get_output_context(
                self.execution_plan,
                self.job_def,
                self.resolved_run_config,
                source_handle,
                self._get_source_run_id(source_handle),
                log_manager=self.log,
                step_context=self,
                resources=None,
                version=version,
                warn_on_step_context_use=True,
            )
        else:
            upstream_output = artificial_output_context

        asset_key = self.job_def.asset_layer.asset_key_for_input(
            node_handle=self.node_handle, input_name=name
        )
        asset_partitions_subset = (
            self.asset_partitions_subset_for_input(name)
            if self.has_asset_partitions_for_input(name)
            else None
        )

        asset_partitions_def = (
            self.job_def.asset_layer.partitions_def_for_asset(asset_key) if asset_key else None
        )
        return InputContext(
            job_name=self.job_def.name,
            name=name,
            op_def=self.op_def,
            config=config,
            metadata=metadata,
            upstream_output=upstream_output,
            dagster_type=dagster_type,
            log_manager=self.log,
            step_context=self,
            resource_config=resource_config,
            resources=resources,
            asset_key=asset_key,
            asset_partitions_subset=asset_partitions_subset,
            asset_partitions_def=asset_partitions_def,
            instance=self.instance,
        )

    def for_hook(self, hook_def: HookDefinition) -> "HookContext":
        from .hook import HookContext

        return HookContext(self, hook_def)

    def get_known_state(self) -> "KnownExecutionState":
        if not self._known_state:
            check.failed(
                "Attempted to access KnownExecutionState but it was not provided at context"
                " creation"
            )
        return self._known_state

    def can_load(
        self,
        step_output_handle: StepOutputHandle,
    ) -> bool:
        # can load from upstream in the same run
        if step_output_handle in self.get_known_state().ready_outputs:
            return True

        if (
            self._should_load_from_previous_runs(step_output_handle)
            # should and can load from a previous run
            and self._get_source_run_id_from_logs(step_output_handle)
        ):
            return True

        return False

    def observe_output(self, output_name: str, mapping_key: Optional[str] = None) -> None:
        if mapping_key:
            if output_name not in self._seen_outputs:
                self._seen_outputs[output_name] = set()
            cast(Set[str], self._seen_outputs[output_name]).add(mapping_key)
        else:
            self._seen_outputs[output_name] = "seen"

    def has_seen_output(self, output_name: str, mapping_key: Optional[str] = None) -> bool:
        if mapping_key:
            return (
                output_name in self._seen_outputs and mapping_key in self._seen_outputs[output_name]
            )
        return output_name in self._seen_outputs

    def add_output_metadata(
        self,
        metadata: Mapping[str, Any],
        output_name: Optional[str] = None,
        mapping_key: Optional[str] = None,
    ) -> None:
        if output_name is None and len(self.op_def.output_defs) == 1:
            output_def = self.op_def.output_defs[0]
            output_name = output_def.name
        elif output_name is None:
            raise DagsterInvariantViolationError(
                "Attempted to log metadata without providing output_name, but multiple outputs"
                " exist. Please provide an output_name to the invocation of"
                " `context.add_output_metadata`."
            )
        else:
            output_def = self.op_def.output_def_named(output_name)

        if self.has_seen_output(output_name, mapping_key):
            output_desc = (
                f"output '{output_def.name}'"
                if not mapping_key
                else f"output '{output_def.name}' with mapping_key '{mapping_key}'"
            )
            raise DagsterInvariantViolationError(
                f"In {self.op_def.node_type_str} '{self.op.name}', attempted to log output"
                f" metadata for {output_desc} which has already been yielded. Metadata must be"
                " logged before the output is yielded."
            )
        if output_def.is_dynamic and not mapping_key:
            raise DagsterInvariantViolationError(
                f"In {self.op_def.node_type_str} '{self.op.name}', attempted to log metadata"
                f" for dynamic output '{output_def.name}' without providing a mapping key. When"
                " logging metadata for a dynamic output, it is necessary to provide a mapping key."
            )

        if mapping_key:
            if output_name not in self._output_metadata:
                self._output_metadata[output_name] = {}
            if mapping_key in self._output_metadata[output_name]:
                self._output_metadata[output_name][mapping_key].update(metadata)
            else:
                self._output_metadata[output_name][mapping_key] = metadata
        else:
            if output_name in self._output_metadata:
                self._output_metadata[output_name].update(metadata)
            else:
                self._output_metadata[output_name] = metadata

    def get_output_metadata(
        self, output_name: str, mapping_key: Optional[str] = None
    ) -> Optional[Mapping[str, Any]]:
        metadata = self._output_metadata.get(output_name)
        if mapping_key and metadata:
            return metadata.get(mapping_key)
        return metadata

    def _get_source_run_id_from_logs(self, step_output_handle: StepOutputHandle) -> Optional[str]:
        # walk through event logs to find the right run_id based on the run lineage

        parent_state = self.get_known_state().parent_state
        while parent_state:
            # if the parent run has yielded an StepOutput event for the given step output,
            # we find the source run id
            if step_output_handle in parent_state.produced_outputs:
                return parent_state.run_id

            # else, keep looking backwards
            parent_state = parent_state.get_parent_state()

        # When a fixed path is provided via io manager, it's able to run step subset using an execution
        # plan when the ascendant outputs were not previously created by dagster-controlled
        # computations. for example, in backfills, with fixed path io manager, we allow users to
        # "re-execute" runs with steps where the outputs weren't previously stored by dagster.

        # Warn about this special case because it will also reach here when all previous runs have
        # skipped yielding this output. From the logs, we have no easy way to differentiate the fixed
        # path case and the skipping case, until we record the skipping info in KnownExecutionState,
        # i.e. resolve https://github.com/dagster-io/dagster/issues/3511
        self.log.warning(
            f"No previously stored outputs found for source {step_output_handle}. "
            "This is either because you are using an IO Manager that does not depend on run ID, "
            "or because all the previous runs have skipped the output in conditional execution."
        )
        return None

    def _should_load_from_previous_runs(self, step_output_handle: StepOutputHandle) -> bool:
        # should not load if not a re-execution
        if self.dagster_run.parent_run_id is None:
            return False
        # should not load if re-executing the entire pipeline
        if self.dagster_run.step_keys_to_execute is None:
            return False

        # should not load if the entire dynamic step is being executed in the current run
        handle = StepHandle.parse_from_key(step_output_handle.step_key)
        if (
            isinstance(handle, ResolvedFromDynamicStepHandle)
            and handle.unresolved_form.to_key() in self.dagster_run.step_keys_to_execute
        ):
            return False

        # should not load if this step is being executed in the current run
        return step_output_handle.step_key not in self.dagster_run.step_keys_to_execute

    def _get_source_run_id(self, step_output_handle: StepOutputHandle) -> Optional[str]:
        if self._should_load_from_previous_runs(step_output_handle):
            return self._get_source_run_id_from_logs(step_output_handle)
        else:
            return self.dagster_run.run_id

    def capture_step_exception(self, exception: BaseException):
        self._step_exception = check.inst_param(exception, "exception", BaseException)

    @property
    def step_exception(self) -> Optional[BaseException]:
        return self._step_exception

    @property
    def step_output_capture(self) -> Optional[Dict[StepOutputHandle, Any]]:
        return self._step_output_capture

    @property
    def previous_attempt_count(self) -> int:
        return self.get_known_state().get_retry_state().get_attempt_count(self._step.key)

    @property
    def op_config(self) -> Any:
        op_config = self.resolved_run_config.ops.get(str(self.node_handle))
        return op_config.config if op_config else None

    @property
    def is_op_in_graph(self) -> bool:
        """Whether this step corresponds to an op within a graph (either @graph, or @graph_asset)."""
        return self.step.node_handle.parent is not None

    @property
    def is_sda_step(self) -> bool:
        """Whether this step corresponds to a software define asset, inferred by presence of asset info on outputs.

        note: ops can materialize assets as well.
        """
        for output in self.step.step_outputs:
            asset_info = self.job_def.asset_layer.asset_info_for_output(
                self.node_handle, output.name
            )
            if asset_info is not None:
                return True
        return False

    def set_data_version(self, asset_key: AssetKey, data_version: "DataVersion") -> None:
        self._data_version_cache[asset_key] = data_version

    def has_data_version(self, asset_key: AssetKey) -> bool:
        return asset_key in self._data_version_cache

    def get_data_version(self, asset_key: AssetKey) -> "DataVersion":
        return self._data_version_cache[asset_key]

    @property
    def input_asset_records(self) -> Optional[Mapping[AssetKey, Optional["InputAssetVersionInfo"]]]:
        return self._input_asset_version_info

    @property
    def is_external_input_asset_version_info_loaded(self) -> bool:
        return self._is_external_input_asset_version_info_loaded

    def get_input_asset_version_info(self, key: AssetKey) -> Optional["InputAssetVersionInfo"]:
        if key not in self._input_asset_version_info:
            self._fetch_input_asset_version_info(key)
        return self._input_asset_version_info[key]

    # "external" refers to records for inputs generated outside of this step
    def fetch_external_input_asset_version_info(self) -> None:
        output_keys = self.get_output_asset_keys()

        all_dep_keys: List[AssetKey] = []
        for output_key in output_keys:
            if output_key not in self.job_def.asset_layer.asset_deps:
                continue
            dep_keys = self.job_def.asset_layer.upstream_assets_for_asset(output_key)
            for key in dep_keys:
                if key not in all_dep_keys and key not in output_keys:
                    all_dep_keys.append(key)

        self._input_asset_version_info = {}
        for key in all_dep_keys:
            self._fetch_input_asset_version_info(key)
        self._is_external_input_asset_version_info_loaded = True

    def _fetch_input_asset_version_info(self, key: AssetKey) -> None:
        from dagster._core.definitions.data_version import (
            extract_data_version_from_entry,
        )

        event = self._get_input_asset_event(key)
        if event is None:
            self._input_asset_version_info[key] = None
        else:
            storage_id = event.storage_id
            # Input name will be none if this is an internal dep
            input_name = self.job_def.asset_layer.input_for_asset_key(self.node_handle, key)
            # Exclude AllPartitionMapping for now to avoid huge queries
            if input_name and self.has_asset_partitions_for_input(input_name):
                subset = self.asset_partitions_subset_for_input(
                    input_name, require_valid_partitions=False
                )
                input_keys = list(subset.get_partition_keys())

                # This check represents a temporary constraint that prevents huge query results for upstream
                # partition data versions from timing out runs. If a partitioned dependency (a) uses an
                # AllPartitionMapping; and (b) has greater than or equal to
                # SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD dependency partitions, then we
                # process it as a non-partitioned dependency (note that this was the behavior for
                # all partition dependencies prior to 2023-08).  This means that stale status
                # results cannot be accurately computed for the dependency, and there is thus
                # corresponding logic in the CachingStaleStatusResolver to account for this. This
                # constraint should be removed when we have thoroughly examined the performance of
                # the data version retrieval query and can guarantee decent performance.
                if len(input_keys) < SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD:
                    data_version = self._get_partitions_data_version_from_keys(key, input_keys)
                else:
                    data_version = extract_data_version_from_entry(event.event_log_entry)
            else:
                data_version = extract_data_version_from_entry(event.event_log_entry)
            self._input_asset_version_info[key] = InputAssetVersionInfo(
                storage_id, data_version, event.run_id, event.timestamp
            )

    def partition_mapping_for_input(self, input_name: str) -> Optional[PartitionMapping]:
        asset_layer = self.job_def.asset_layer
        upstream_asset_key = asset_layer.asset_key_for_input(self.node_handle, input_name)
        if upstream_asset_key:
            upstream_asset_partitions_def = asset_layer.partitions_def_for_asset(upstream_asset_key)
            assets_def = asset_layer.assets_def_for_node(self.node_handle)
            partitions_def = assets_def.partitions_def if assets_def else None
            explicit_partition_mapping = self.job_def.asset_layer.partition_mapping_for_node_input(
                self.node_handle, upstream_asset_key
            )
            return infer_partition_mapping(
                explicit_partition_mapping,
                partitions_def,
                upstream_asset_partitions_def,
            )
        else:
            return None

    def _get_input_asset_event(self, key: AssetKey) -> Optional["EventLogRecord"]:
        event = self.instance.get_latest_data_version_record(key)
        if event:
            self._check_input_asset_event(key, event)
        return event

    def _check_input_asset_event(self, key: AssetKey, event: "EventLogRecord") -> None:
        assert event.event_log_entry
        event_data_version = extract_data_version_from_entry(event.event_log_entry)
        if key in self._data_version_cache and self._data_version_cache[key] != event_data_version:
            self.log.warning(
                f"Data version mismatch for asset {key}. Data version from materialization within"
                f" current step is `{self._data_version_cache[key]}`. Data version from most recent"
                f" materialization is `{event_data_version}`. Most recent materialization will be"
                " used for provenance tracking."
            )

    def _get_partitions_data_version_from_keys(
        self, key: AssetKey, partition_keys: Sequence[str]
    ) -> "DataVersion":
        from dagster._core.definitions.data_version import (
            DataVersion,
        )
        from dagster._core.events import DagsterEventType

        # TODO: this needs to account for observations also
        event_type = DagsterEventType.ASSET_MATERIALIZATION
        tags_by_partition = (
            self.instance._event_storage.get_latest_tags_by_partition(  # noqa: SLF001
                key, event_type, [DATA_VERSION_TAG], asset_partitions=list(partition_keys)
            )
        )
        partition_data_versions = [
            pair[1][DATA_VERSION_TAG]
            for pair in sorted(tags_by_partition.items(), key=lambda x: x[0])
        ]
        hash_sig = sha256()
        hash_sig.update(bytearray("".join(partition_data_versions), "utf8"))
        return DataVersion(hash_sig.hexdigest())

    # Call this to clear the cache for an input asset record. This is necessary when an old
    # materialization for an asset was loaded during `fetch_external_input_asset_records` because an
    # intrastep asset is not required, but then that asset is materialized during the step. If we
    # don't clear the cache for this asset, then we won't use the most up-to-date asset record.
    def wipe_input_asset_version_info(self, key: AssetKey) -> None:
        if key in self._input_asset_version_info:
            del self._input_asset_version_info[key]

    def get_output_asset_keys(self) -> AbstractSet[AssetKey]:
        output_keys: Set[AssetKey] = set()
        for step_output in self.step.step_outputs:
            asset_info = self.job_def.asset_layer.asset_info_for_output(
                self.node_handle, step_output.name
            )
            if asset_info is None or not asset_info.is_required:
                continue
            output_keys.add(asset_info.key)
        return output_keys

    def has_asset_partitions_for_input(self, input_name: str) -> bool:
        asset_layer = self.job_def.asset_layer
        upstream_asset_key = asset_layer.asset_key_for_input(self.node_handle, input_name)

        return (
            upstream_asset_key is not None
            and asset_layer.partitions_def_for_asset(upstream_asset_key) is not None
        )

    def asset_partition_key_range_for_input(self, input_name: str) -> PartitionKeyRange:
        subset = self.asset_partitions_subset_for_input(input_name)
        partition_key_ranges = subset.get_partition_key_ranges(
            dynamic_partitions_store=self.instance
        )

        if len(partition_key_ranges) != 1:
            check.failed(
                "Tried to access asset partition key range, but there are "
                f"({len(partition_key_ranges)}) key ranges associated with this input.",
            )

        return partition_key_ranges[0]

    def asset_partitions_subset_for_input(
        self, input_name: str, *, require_valid_partitions: bool = True
    ) -> PartitionsSubset:
        asset_layer = self.job_def.asset_layer
        assets_def = asset_layer.assets_def_for_node(self.node_handle)
        upstream_asset_key = asset_layer.asset_key_for_input(self.node_handle, input_name)

        if upstream_asset_key is not None:
            upstream_asset_partitions_def = asset_layer.partitions_def_for_asset(upstream_asset_key)

            if upstream_asset_partitions_def is not None:
                partitions_def = assets_def.partitions_def if assets_def else None
                partitions_subset = (
                    partitions_def.empty_subset().with_partition_key_range(
                        self.asset_partition_key_range, dynamic_partitions_store=self.instance
                    )
                    if partitions_def
                    else None
                )
                partition_mapping = infer_partition_mapping(
                    asset_layer.partition_mapping_for_node_input(
                        self.node_handle, upstream_asset_key
                    ),
                    partitions_def,
                    upstream_asset_partitions_def,
                )
                mapped_partitions_result = (
                    partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
                        partitions_subset,
                        upstream_asset_partitions_def,
                        dynamic_partitions_store=self.instance,
                    )
                )

                if (
                    require_valid_partitions
                    and mapped_partitions_result.required_but_nonexistent_partition_keys
                ):
                    raise DagsterInvariantViolationError(
                        f"Partition key range {self.asset_partition_key_range} in"
                        f" {self.node_handle.name} depends on invalid partition keys"
                        f" {mapped_partitions_result.required_but_nonexistent_partition_keys} in"
                        f" upstream asset {upstream_asset_key}"
                    )

                return mapped_partitions_result.partitions_subset

        check.failed("The input has no asset partitions")

    def asset_partition_key_for_input(self, input_name: str) -> str:
        start, end = self.asset_partition_key_range_for_input(input_name)
        if start == end:
            return start
        else:
            check.failed(
                f"Tried to access partition key for input '{input_name}' of step '{self.step.key}',"
                f" but the step input has a partition range: '{start}' to '{end}'."
            )

    def _partitions_def_for_output(self, output_name: str) -> Optional[PartitionsDefinition]:
        asset_info = self.job_def.asset_layer.asset_info_for_output(
            node_handle=self.node_handle, output_name=output_name
        )
        if asset_info:
            return asset_info.partitions_def
        else:
            return None

    def partitions_def_for_output(self, output_name: str) -> Optional[PartitionsDefinition]:
        return self._partitions_def_for_output(output_name)

    def has_asset_partitions_for_output(self, output_name: str) -> bool:
        return self._partitions_def_for_output(output_name) is not None

    def asset_partition_key_range_for_output(self, output_name: str) -> PartitionKeyRange:
        if self._partitions_def_for_output(output_name) is not None:
            return self.asset_partition_key_range

        check.failed("The output has no asset partitions")

    def asset_partition_key_for_output(self, output_name: str) -> str:
        start, end = self.asset_partition_key_range_for_output(output_name)
        if start == end:
            return start
        else:
            check.failed(
                f"Tried to access partition key for output '{output_name}' of step"
                f" '{self.step.key}', but the step output has a partition range: '{start}' to"
                f" '{end}'."
            )

    def asset_partitions_time_window_for_output(self, output_name: str) -> TimeWindow:
        """The time window for the partitions of the asset correponding to the given output.

        Raises an error if either of the following are true:
        - The output asset has no partitioning.
        - The output asset is not partitioned with a TimeWindowPartitionsDefinition or a
          MultiPartitionsDefinition with one time-partitioned dimension.
        """
        partitions_def = self._partitions_def_for_output(output_name)

        if not partitions_def:
            raise ValueError(
                "Tried to get asset partitions for an output that does not correspond to a "
                "partitioned asset."
            )

        if not has_one_dimension_time_window_partitioning(partitions_def):
            raise ValueError(
                "Tried to get asset partitions for an output that correponds to a partitioned "
                "asset that is not time-partitioned."
            )

        partitions_def = cast(
            Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition], partitions_def
        )
        partition_key_range = self.asset_partition_key_range_for_output(output_name)
        return TimeWindow(
            # mypy thinks partitions_def is <nothing> here because ????
            partitions_def.time_window_for_partition_key(partition_key_range.start).start,
            partitions_def.time_window_for_partition_key(partition_key_range.end).end,
        )

    def asset_partitions_time_window_for_input(self, input_name: str) -> TimeWindow:
        """The time window for the partitions of the asset correponding to the given input.

        Raises an error if either of the following are true:
        - The input asset has no partitioning.
        - The input asset is not partitioned with a TimeWindowPartitionsDefinition or a
          MultiPartitionsDefinition with one time-partitioned dimension.
        """
        asset_layer = self.job_def.asset_layer
        upstream_asset_key = asset_layer.asset_key_for_input(self.node_handle, input_name)

        if upstream_asset_key is None:
            raise ValueError("The input has no corresponding asset")

        upstream_asset_partitions_def = asset_layer.partitions_def_for_asset(upstream_asset_key)

        if not upstream_asset_partitions_def:
            raise ValueError(
                "Tried to get asset partitions for an input that does not correspond to a "
                "partitioned asset."
            )

        if not has_one_dimension_time_window_partitioning(upstream_asset_partitions_def):
            raise ValueError(
                "Tried to get asset partitions for an input that correponds to a partitioned "
                "asset that is not time-partitioned."
            )

        upstream_asset_partitions_def = cast(
            Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition],
            upstream_asset_partitions_def,
        )
        partition_key_range = self.asset_partition_key_range_for_input(input_name)

        return TimeWindow(
            upstream_asset_partitions_def.time_window_for_partition_key(
                partition_key_range.start
            ).start,
            upstream_asset_partitions_def.time_window_for_partition_key(
                partition_key_range.end
            ).end,
        )

    def get_type_loader_context(self) -> "DagsterTypeLoaderContext":
        return DagsterTypeLoaderContext(
            plan_data=self.plan_data,
            execution_data=self._execution_data,
            log_manager=self._log_manager,
            step=self.step,
            output_capture=self._output_capture,
            known_state=self._known_state,
        )


class TypeCheckContext:
    """The ``context`` object available to a type check function on a DagsterType."""

    def __init__(
        self,
        run_id: str,
        log_manager: DagsterLogManager,
        scoped_resources_builder: ScopedResourcesBuilder,
        dagster_type: DagsterType,
    ):
        self._run_id = run_id
        self._log = log_manager
        self._resources = scoped_resources_builder.build(dagster_type.required_resource_keys)

    @public
    @property
    def resources(self) -> "Resources":
        """An object whose attributes contain the resources available to this op."""
        return self._resources

    @public
    @property
    def run_id(self) -> str:
        """The id of this job run."""
        return self._run_id

    @public
    @property
    def log(self) -> DagsterLogManager:
        """Centralized log dispatch from user code."""
        return self._log


class DagsterTypeLoaderContext(StepExecutionContext):
    """The context object provided to a :py:class:`@dagster_type_loader <dagster_type_loader>`-decorated function during execution.

    Users should not construct this object directly.
    """

    @public
    @property
    def resources(self) -> "Resources":
        """The resources available to the type loader, specified by the `required_resource_keys` argument of the decorator."""
        return super(DagsterTypeLoaderContext, self).resources

    @public
    @property
    def job_def(self) -> "JobDefinition":
        """The underlying job definition being executed."""
        return super(DagsterTypeLoaderContext, self).job_def

    @public
    @property
    def op_def(self) -> "OpDefinition":
        """The op for which type loading is occurring."""
        return super(DagsterTypeLoaderContext, self).op_def
