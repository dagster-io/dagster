"""Structured representations of system events."""
import logging
import os
import sys
from enum import Enum
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Type,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    ExpectationResult,
    HookDefinition,
    Materialization,
    MetadataEntry,
    NodeHandle,
)
from dagster._core.definitions.events import AssetLineageInfo, ObjectStoreOperationType
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.errors import DagsterError, HookExecutionError
from dagster._core.execution.context.hook import HookContext
from dagster._core.execution.context.system import (
    IPlanContext,
    IStepContext,
    PlanExecutionContext,
    PlanOrchestrationContext,
    StepExecutionContext,
)
from dagster._core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster._core.execution.plan.inputs import StepInputData
from dagster._core.execution.plan.objects import StepFailureData, StepRetryData, StepSuccessData
from dagster._core.execution.plan.outputs import StepOutputData
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.pipeline_run import PipelineRunStatus
from dagster._serdes import (
    DefaultNamedTupleSerializer,
    WhitelistMap,
    register_serdes_tuple_fallbacks,
    whitelist_for_serdes,
)
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.timing import format_duration

if TYPE_CHECKING:
    from dagster._core.definitions.events import ObjectStoreOperation
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.step import ExecutionStep, StepKind

EventSpecificData = Union[
    StepOutputData,
    StepFailureData,
    StepSuccessData,
    "StepMaterializationData",
    "StepExpectationResultData",
    StepInputData,
    "EngineEventData",
    "HookErroredData",
    StepRetryData,
    "PipelineFailureData",
    "PipelineCanceledData",
    "ObjectStoreOperationResultData",
    "HandledOutputData",
    "LoadedInputData",
    "ComputeLogsCaptureData",
    "AssetObservationData",
    "AssetMaterializationPlannedData",
]


class DagsterEventType(Enum):
    """The types of events that may be yielded by solid and pipeline execution."""

    STEP_OUTPUT = "STEP_OUTPUT"
    STEP_INPUT = "STEP_INPUT"
    STEP_FAILURE = "STEP_FAILURE"
    STEP_START = "STEP_START"
    STEP_SUCCESS = "STEP_SUCCESS"
    STEP_SKIPPED = "STEP_SKIPPED"

    # The process carrying out step execution is starting/started. Shown as a
    # marker start/end in Dagit
    STEP_WORKER_STARTING = "STEP_WORKER_STARTING"
    STEP_WORKER_STARTED = "STEP_WORKER_STARTED"

    # Resource initialization for execution has started/succeede/failed. Shown
    # as a marker start/end in Dagit
    RESOURCE_INIT_STARTED = "RESOURCE_INIT_STARTED"
    RESOURCE_INIT_SUCCESS = "RESOURCE_INIT_SUCCESS"
    RESOURCE_INIT_FAILURE = "RESOURCE_INIT_FAILURE"

    STEP_UP_FOR_RETRY = "STEP_UP_FOR_RETRY"  # "failed" but want to retry
    STEP_RESTARTED = "STEP_RESTARTED"

    ASSET_MATERIALIZATION = "ASSET_MATERIALIZATION"
    ASSET_MATERIALIZATION_PLANNED = "ASSET_MATERIALIZATION_PLANNED"
    ASSET_OBSERVATION = "ASSET_OBSERVATION"
    STEP_EXPECTATION_RESULT = "STEP_EXPECTATION_RESULT"

    # We want to display RUN_* events in dagit and in our LogManager output, but in order to
    # support backcompat for our storage layer, we need to keep the persisted value to be strings
    # of the form "PIPELINE_*".  We may have user code that pass in the DagsterEventType
    # enum values into storage APIs (like get_event_records, which takes in an EventRecordsFilter).
    RUN_ENQUEUED = "PIPELINE_ENQUEUED"
    RUN_DEQUEUED = "PIPELINE_DEQUEUED"
    RUN_STARTING = "PIPELINE_STARTING"  # Launch is happening, execution hasn't started yet
    RUN_START = "PIPELINE_START"  # Execution has started
    RUN_SUCCESS = "PIPELINE_SUCCESS"
    RUN_FAILURE = "PIPELINE_FAILURE"
    RUN_CANCELING = "PIPELINE_CANCELING"
    RUN_CANCELED = "PIPELINE_CANCELED"

    # Keep these legacy enum values around, to keep back-compatability for user code that might be
    # using these constants to filter event records
    PIPELINE_ENQUEUED = RUN_ENQUEUED
    PIPELINE_DEQUEUED = RUN_DEQUEUED
    PIPELINE_STARTING = RUN_STARTING
    PIPELINE_START = RUN_START
    PIPELINE_SUCCESS = RUN_SUCCESS
    PIPELINE_FAILURE = RUN_FAILURE
    PIPELINE_CANCELING = RUN_CANCELING
    PIPELINE_CANCELED = RUN_CANCELED

    OBJECT_STORE_OPERATION = "OBJECT_STORE_OPERATION"
    ASSET_STORE_OPERATION = "ASSET_STORE_OPERATION"
    LOADED_INPUT = "LOADED_INPUT"
    HANDLED_OUTPUT = "HANDLED_OUTPUT"

    ENGINE_EVENT = "ENGINE_EVENT"

    HOOK_COMPLETED = "HOOK_COMPLETED"
    HOOK_ERRORED = "HOOK_ERRORED"
    HOOK_SKIPPED = "HOOK_SKIPPED"

    ALERT_START = "ALERT_START"
    ALERT_SUCCESS = "ALERT_SUCCESS"
    ALERT_FAILURE = "ALERT_FAILURE"

    LOGS_CAPTURED = "LOGS_CAPTURED"


EVENT_TYPE_VALUE_TO_DISPLAY_STRING = {
    "PIPELINE_ENQUEUED": "RUN_ENQUEUED",
    "PIPELINE_DEQUEUED": "RUN_DEQUEUED",
    "PIPELINE_STARTING": "RUN_STARTING",
    "PIPELINE_START": "RUN_START",
    "PIPELINE_SUCCESS": "RUN_SUCCESS",
    "PIPELINE_FAILURE": "RUN_FAILURE",
    "PIPELINE_CANCELING": "RUN_CANCELING",
    "PIPELINE_CANCELED": "RUN_CANCELED",
}

STEP_EVENTS = {
    DagsterEventType.STEP_INPUT,
    DagsterEventType.STEP_START,
    DagsterEventType.STEP_OUTPUT,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.STEP_SUCCESS,
    DagsterEventType.STEP_SKIPPED,
    DagsterEventType.ASSET_MATERIALIZATION,
    DagsterEventType.ASSET_OBSERVATION,
    DagsterEventType.STEP_EXPECTATION_RESULT,
    DagsterEventType.OBJECT_STORE_OPERATION,
    DagsterEventType.HANDLED_OUTPUT,
    DagsterEventType.LOADED_INPUT,
    DagsterEventType.STEP_RESTARTED,
    DagsterEventType.STEP_UP_FOR_RETRY,
}

FAILURE_EVENTS = {
    DagsterEventType.RUN_FAILURE,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.RUN_CANCELED,
}

PIPELINE_EVENTS = {
    DagsterEventType.RUN_ENQUEUED,
    DagsterEventType.RUN_DEQUEUED,
    DagsterEventType.RUN_STARTING,
    DagsterEventType.RUN_START,
    DagsterEventType.RUN_SUCCESS,
    DagsterEventType.RUN_FAILURE,
    DagsterEventType.RUN_CANCELING,
    DagsterEventType.RUN_CANCELED,
}

HOOK_EVENTS = {
    DagsterEventType.HOOK_COMPLETED,
    DagsterEventType.HOOK_ERRORED,
    DagsterEventType.HOOK_SKIPPED,
}

ALERT_EVENTS = {
    DagsterEventType.ALERT_START,
    DagsterEventType.ALERT_SUCCESS,
    DagsterEventType.ALERT_FAILURE,
}

MARKER_EVENTS = {
    DagsterEventType.ENGINE_EVENT,
    DagsterEventType.STEP_WORKER_STARTING,
    DagsterEventType.STEP_WORKER_STARTED,
    DagsterEventType.RESOURCE_INIT_STARTED,
    DagsterEventType.RESOURCE_INIT_SUCCESS,
    DagsterEventType.RESOURCE_INIT_FAILURE,
}


EVENT_TYPE_TO_PIPELINE_RUN_STATUS = {
    DagsterEventType.RUN_START: PipelineRunStatus.STARTED,
    DagsterEventType.RUN_SUCCESS: PipelineRunStatus.SUCCESS,
    DagsterEventType.RUN_FAILURE: PipelineRunStatus.FAILURE,
    DagsterEventType.RUN_ENQUEUED: PipelineRunStatus.QUEUED,
    DagsterEventType.RUN_STARTING: PipelineRunStatus.STARTING,
    DagsterEventType.RUN_CANCELING: PipelineRunStatus.CANCELING,
    DagsterEventType.RUN_CANCELED: PipelineRunStatus.CANCELED,
}

PIPELINE_RUN_STATUS_TO_EVENT_TYPE = {v: k for k, v in EVENT_TYPE_TO_PIPELINE_RUN_STATUS.items()}

ASSET_EVENTS = {
    DagsterEventType.ASSET_MATERIALIZATION,
    DagsterEventType.ASSET_OBSERVATION,
    DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
}


def _assert_type(
    method: str,
    expected_type: Union[DagsterEventType, List[DagsterEventType]],
    actual_type: DagsterEventType,
) -> None:
    if not isinstance(expected_type, list):
        expected_type = [expected_type]

    check.invariant(
        actual_type in expected_type,
        f"{method} only callable when event_type is {','.join([t.value for t in expected_type])}, called on {actual_type}",
    )


def _validate_event_specific_data(
    event_type: DagsterEventType, event_specific_data: Optional["EventSpecificData"]
) -> Optional["EventSpecificData"]:

    if event_type == DagsterEventType.STEP_OUTPUT:
        check.inst_param(event_specific_data, "event_specific_data", StepOutputData)
    elif event_type == DagsterEventType.STEP_FAILURE:
        check.inst_param(event_specific_data, "event_specific_data", StepFailureData)
    elif event_type == DagsterEventType.STEP_SUCCESS:
        check.inst_param(event_specific_data, "event_specific_data", StepSuccessData)
    elif event_type == DagsterEventType.ASSET_MATERIALIZATION:
        check.inst_param(event_specific_data, "event_specific_data", StepMaterializationData)
    elif event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        check.inst_param(event_specific_data, "event_specific_data", StepExpectationResultData)
    elif event_type == DagsterEventType.STEP_INPUT:
        check.inst_param(event_specific_data, "event_specific_data", StepInputData)
    elif event_type in (
        DagsterEventType.ENGINE_EVENT,
        DagsterEventType.STEP_WORKER_STARTING,
        DagsterEventType.STEP_WORKER_STARTED,
        DagsterEventType.RESOURCE_INIT_STARTED,
        DagsterEventType.RESOURCE_INIT_SUCCESS,
        DagsterEventType.RESOURCE_INIT_FAILURE,
    ):
        check.inst_param(event_specific_data, "event_specific_data", EngineEventData)
    elif event_type == DagsterEventType.HOOK_ERRORED:
        check.inst_param(event_specific_data, "event_specific_data", HookErroredData)
    elif event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED:
        check.inst_param(
            event_specific_data, "event_specific_data", AssetMaterializationPlannedData
        )

    return event_specific_data


def log_step_event(step_context: IStepContext, event: "DagsterEvent") -> None:
    event_type = DagsterEventType(event.event_type_value)
    log_level = logging.ERROR if event_type in FAILURE_EVENTS else logging.DEBUG

    step_context.log.log_dagster_event(
        level=log_level,
        msg=event.message or f"{event_type} for step {step_context.step.key}",
        dagster_event=event,
    )


def log_pipeline_event(pipeline_context: IPlanContext, event: "DagsterEvent") -> None:
    event_type = DagsterEventType(event.event_type_value)
    log_level = logging.ERROR if event_type in FAILURE_EVENTS else logging.DEBUG

    pipeline_context.log.log_dagster_event(
        level=log_level,
        msg=event.message or f"{event_type} for pipeline {pipeline_context.pipeline_name}",
        dagster_event=event,
    )


def log_resource_event(log_manager: DagsterLogManager, event: "DagsterEvent") -> None:
    event_specific_data = cast(EngineEventData, event.event_specific_data)

    log_level = logging.ERROR if event_specific_data.error else logging.DEBUG
    log_manager.log_dagster_event(level=log_level, msg=event.message or "", dagster_event=event)


class DagsterEventSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type,
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> NamedTuple:
        event_type_value = storage_dict["event_type_value"]
        pipeline_name = storage_dict["pipeline_name"]
        message = storage_dict.get("message")
        step_key = storage_dict.get("step_key")
        event_specific_data = storage_dict.get("event_specific_data")

        event_type_value, event_specific_data = _handle_back_compat(
            event_type_value, event_specific_data
        )
        storage_dict["event_type_value"] = event_type_value
        storage_dict["event_specific_data"] = event_specific_data

        try:
            return super().value_from_storage_dict(
                storage_dict, klass, args_for_class, whitelist_map, descent_path
            )
        except Exception:
            new_message = (
                f"Could not deserialize event of type {event_type_value}. This event may have been written by a newer version of Dagster."
                + (f' Original message: "{message}"' if message else "")
            )
            return DagsterEvent(
                event_type_value=DagsterEventType.ENGINE_EVENT.value,
                pipeline_name=pipeline_name,
                message=new_message,
                step_key=step_key,
                event_specific_data=EngineEventData(
                    error=serializable_error_info_from_exc_info(sys.exc_info())
                ),
            )


@whitelist_for_serdes(serializer=DagsterEventSerializer)
class DagsterEvent(
    NamedTuple(
        "_DagsterEvent",
        [
            ("event_type_value", str),
            ("pipeline_name", str),
            ("step_handle", Optional[Union[StepHandle, ResolvedFromDynamicStepHandle]]),
            ("solid_handle", Optional[NodeHandle]),
            ("step_kind_value", Optional[str]),
            ("logging_tags", Optional[Dict[str, str]]),
            ("event_specific_data", Optional["EventSpecificData"]),
            ("message", Optional[str]),
            ("pid", Optional[int]),
            ("step_key", Optional[str]),
        ],
    )
):
    """Events yielded by solid and pipeline execution.

    Users should not instantiate this class.

    Attributes:
        event_type_value (str): Value for a DagsterEventType.
        pipeline_name (str)
        solid_handle (NodeHandle)
        step_kind_value (str): Value for a StepKind.
        logging_tags (Dict[str, str])
        event_specific_data (Any): Type must correspond to event_type_value.
        message (str)
        pid (int)
        step_key (Optional[str]): DEPRECATED
    """

    @staticmethod
    def from_step(
        event_type: "DagsterEventType",
        step_context: IStepContext,
        event_specific_data: Optional["EventSpecificData"] = None,
        message: Optional[str] = None,
    ) -> "DagsterEvent":

        event = DagsterEvent(
            event_type_value=check.inst_param(event_type, "event_type", DagsterEventType).value,
            pipeline_name=step_context.pipeline_name,
            step_handle=step_context.step.handle,
            solid_handle=step_context.step.solid_handle,
            step_kind_value=step_context.step.kind.value,
            logging_tags=step_context.logging_tags,
            event_specific_data=_validate_event_specific_data(event_type, event_specific_data),
            message=check.opt_str_param(message, "message"),
            pid=os.getpid(),
        )

        log_step_event(step_context, event)

        return event

    @staticmethod
    def from_pipeline(
        event_type: DagsterEventType,
        pipeline_context: IPlanContext,
        message: Optional[str] = None,
        event_specific_data: Optional["EventSpecificData"] = None,
        step_handle: Optional[Union[StepHandle, ResolvedFromDynamicStepHandle]] = None,
    ) -> "DagsterEvent":
        check.opt_inst_param(
            step_handle, "step_handle", (StepHandle, ResolvedFromDynamicStepHandle)
        )

        event = DagsterEvent(
            event_type_value=check.inst_param(event_type, "event_type", DagsterEventType).value,
            pipeline_name=pipeline_context.pipeline_name,
            message=check.opt_str_param(message, "message"),
            event_specific_data=_validate_event_specific_data(event_type, event_specific_data),
            step_handle=step_handle,
            pid=os.getpid(),
        )

        log_pipeline_event(pipeline_context, event)

        return event

    @staticmethod
    def from_resource(
        event_type: DagsterEventType,
        pipeline_name: str,
        execution_plan: "ExecutionPlan",
        log_manager: DagsterLogManager,
        message: Optional[str] = None,
        event_specific_data: Optional["EngineEventData"] = None,
    ) -> "DagsterEvent":

        event = DagsterEvent(
            event_type_value=check.inst_param(event_type, "event_type", DagsterEventType).value,
            pipeline_name=pipeline_name,
            message=check.opt_str_param(message, "message"),
            event_specific_data=_validate_event_specific_data(
                DagsterEventType.ENGINE_EVENT, event_specific_data
            ),
            step_handle=execution_plan.step_handle_for_single_step_plans(),
            pid=os.getpid(),
        )
        log_resource_event(log_manager, event)
        return event

    def __new__(
        cls,
        event_type_value: str,
        pipeline_name: str,
        step_handle: Optional[Union[StepHandle, ResolvedFromDynamicStepHandle]] = None,
        solid_handle: Optional[NodeHandle] = None,
        step_kind_value: Optional[str] = None,
        logging_tags: Optional[Dict[str, str]] = None,
        event_specific_data: Optional["EventSpecificData"] = None,
        message: Optional[str] = None,
        pid: Optional[int] = None,
        # legacy
        step_key: Optional[str] = None,
    ):
        # old events may contain solid_handle but not step_handle
        if solid_handle is not None and step_handle is None:
            step_handle = StepHandle(solid_handle)

        # Legacy events may have step_key set directly, preserve those to stay in sync
        # with legacy execution plan snapshots.
        if step_handle is not None and step_key is None:
            step_key = step_handle.to_key()

        return super(DagsterEvent, cls).__new__(
            cls,
            check.str_param(event_type_value, "event_type_value"),
            check.str_param(pipeline_name, "pipeline_name"),
            check.opt_inst_param(
                step_handle, "step_handle", (StepHandle, ResolvedFromDynamicStepHandle)
            ),
            check.opt_inst_param(solid_handle, "solid_handle", NodeHandle),
            check.opt_str_param(step_kind_value, "step_kind_value"),
            check.opt_dict_param(logging_tags, "logging_tags"),
            _validate_event_specific_data(DagsterEventType(event_type_value), event_specific_data),
            check.opt_str_param(message, "message"),
            check.opt_int_param(pid, "pid"),
            check.opt_str_param(step_key, "step_key"),
        )

    @property
    def solid_name(self) -> str:
        check.invariant(self.solid_handle is not None)
        solid_handle = cast(NodeHandle, self.solid_handle)
        return solid_handle.name

    @public  # type: ignore
    @property
    def event_type(self) -> DagsterEventType:
        """DagsterEventType: The type of this event."""
        return DagsterEventType(self.event_type_value)

    @public  # type: ignore
    @property
    def is_step_event(self) -> bool:
        return self.event_type in STEP_EVENTS

    @public  # type: ignore
    @property
    def is_hook_event(self) -> bool:
        return self.event_type in HOOK_EVENTS

    @public  # type: ignore
    @property
    def is_alert_event(self) -> bool:
        return self.event_type in ALERT_EVENTS

    @property
    def step_kind(self) -> "StepKind":
        from dagster._core.execution.plan.step import StepKind

        return StepKind(self.step_kind_value)

    @public  # type: ignore
    @property
    def is_step_success(self) -> bool:
        return self.event_type == DagsterEventType.STEP_SUCCESS

    @public  # type: ignore
    @property
    def is_successful_output(self) -> bool:
        return self.event_type == DagsterEventType.STEP_OUTPUT

    @public  # type: ignore
    @property
    def is_step_start(self) -> bool:
        return self.event_type == DagsterEventType.STEP_START

    @public  # type: ignore
    @property
    def is_step_failure(self) -> bool:
        return self.event_type == DagsterEventType.STEP_FAILURE

    @public  # type: ignore
    @property
    def is_resource_init_failure(self) -> bool:
        return self.event_type == DagsterEventType.RESOURCE_INIT_FAILURE

    @public  # type: ignore
    @property
    def is_step_skipped(self) -> bool:
        return self.event_type == DagsterEventType.STEP_SKIPPED

    @public  # type: ignore
    @property
    def is_step_up_for_retry(self) -> bool:
        return self.event_type == DagsterEventType.STEP_UP_FOR_RETRY

    @public  # type: ignore
    @property
    def is_step_restarted(self) -> bool:
        return self.event_type == DagsterEventType.STEP_RESTARTED

    @property
    def is_pipeline_success(self) -> bool:
        return self.event_type == DagsterEventType.RUN_SUCCESS

    @property
    def is_pipeline_failure(self) -> bool:
        return self.event_type == DagsterEventType.RUN_FAILURE

    @public  # type: ignore
    @property
    def is_failure(self) -> bool:
        return self.event_type in FAILURE_EVENTS

    @property
    def is_pipeline_event(self) -> bool:
        return self.event_type in PIPELINE_EVENTS

    @public  # type: ignore
    @property
    def is_engine_event(self) -> bool:
        return self.event_type == DagsterEventType.ENGINE_EVENT

    @public  # type: ignore
    @property
    def is_handled_output(self) -> bool:
        return self.event_type == DagsterEventType.HANDLED_OUTPUT

    @public  # type: ignore
    @property
    def is_loaded_input(self) -> bool:
        return self.event_type == DagsterEventType.LOADED_INPUT

    @public  # type: ignore
    @property
    def is_step_materialization(self) -> bool:
        return self.event_type == DagsterEventType.ASSET_MATERIALIZATION

    @public  # type: ignore
    @property
    def is_expectation_result(self) -> bool:
        return self.event_type == DagsterEventType.STEP_EXPECTATION_RESULT

    @public  # type: ignore
    @property
    def is_asset_observation(self) -> bool:
        return self.event_type == DagsterEventType.ASSET_OBSERVATION

    @public  # type: ignore
    @property
    def is_asset_materialization_planned(self) -> bool:
        return self.event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED

    @public  # type: ignore
    @property
    def asset_key(self) -> Optional[AssetKey]:
        if self.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            return self.step_materialization_data.materialization.asset_key
        elif self.event_type == DagsterEventType.ASSET_OBSERVATION:
            return self.asset_observation_data.asset_observation.asset_key
        elif self.event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED:
            return self.asset_materialization_planned_data.asset_key
        else:
            return None

    @public  # type: ignore
    @property
    def partition(self) -> Optional[str]:
        if self.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            return self.step_materialization_data.materialization.partition
        elif self.event_type == DagsterEventType.ASSET_OBSERVATION:
            return self.asset_observation_data.asset_observation.partition
        else:
            return None

    @property
    def step_input_data(self) -> "StepInputData":
        _assert_type("step_input_data", DagsterEventType.STEP_INPUT, self.event_type)
        return cast(StepInputData, self.event_specific_data)

    @property
    def step_output_data(self) -> StepOutputData:
        _assert_type("step_output_data", DagsterEventType.STEP_OUTPUT, self.event_type)
        return cast(StepOutputData, self.event_specific_data)

    @property
    def step_success_data(self) -> "StepSuccessData":
        _assert_type("step_success_data", DagsterEventType.STEP_SUCCESS, self.event_type)
        return cast(StepSuccessData, self.event_specific_data)

    @property
    def step_failure_data(self) -> "StepFailureData":
        _assert_type("step_failure_data", DagsterEventType.STEP_FAILURE, self.event_type)
        return cast(StepFailureData, self.event_specific_data)

    @property
    def step_retry_data(self) -> "StepRetryData":
        _assert_type("step_retry_data", DagsterEventType.STEP_UP_FOR_RETRY, self.event_type)
        return cast(StepRetryData, self.event_specific_data)

    @property
    def step_materialization_data(self) -> "StepMaterializationData":
        _assert_type(
            "step_materialization_data", DagsterEventType.ASSET_MATERIALIZATION, self.event_type
        )
        return cast(StepMaterializationData, self.event_specific_data)

    @property
    def asset_observation_data(self) -> "AssetObservationData":
        _assert_type("asset_observation_data", DagsterEventType.ASSET_OBSERVATION, self.event_type)
        return cast(AssetObservationData, self.event_specific_data)

    @property
    def asset_materialization_planned_data(self) -> "AssetMaterializationPlannedData":
        _assert_type(
            "asset_materialization_planned",
            DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            self.event_type,
        )
        return cast(AssetMaterializationPlannedData, self.event_specific_data)

    @property
    def step_expectation_result_data(self) -> "StepExpectationResultData":
        _assert_type(
            "step_expectation_result_data",
            DagsterEventType.STEP_EXPECTATION_RESULT,
            self.event_type,
        )
        return cast(StepExpectationResultData, self.event_specific_data)

    @property
    def pipeline_failure_data(self) -> "PipelineFailureData":
        _assert_type("pipeline_failure_data", DagsterEventType.RUN_FAILURE, self.event_type)
        return cast(PipelineFailureData, self.event_specific_data)

    @property
    def engine_event_data(self) -> "EngineEventData":
        _assert_type(
            "engine_event_data",
            [
                DagsterEventType.ENGINE_EVENT,
                DagsterEventType.RESOURCE_INIT_STARTED,
                DagsterEventType.RESOURCE_INIT_SUCCESS,
                DagsterEventType.RESOURCE_INIT_FAILURE,
                DagsterEventType.STEP_WORKER_STARTED,
                DagsterEventType.STEP_WORKER_STARTING,
            ],
            self.event_type,
        )
        return cast(EngineEventData, self.event_specific_data)

    @property
    def hook_completed_data(self) -> Optional["EventSpecificData"]:
        _assert_type("hook_completed_data", DagsterEventType.HOOK_COMPLETED, self.event_type)
        return self.event_specific_data

    @property
    def hook_errored_data(self) -> "HookErroredData":
        _assert_type("hook_errored_data", DagsterEventType.HOOK_ERRORED, self.event_type)
        return cast(HookErroredData, self.event_specific_data)

    @property
    def hook_skipped_data(self) -> Optional["EventSpecificData"]:
        _assert_type("hook_skipped_data", DagsterEventType.HOOK_SKIPPED, self.event_type)
        return self.event_specific_data

    @property
    def logs_captured_data(self):
        _assert_type("logs_captured_data", DagsterEventType.LOGS_CAPTURED, self.event_type)
        return self.event_specific_data

    @staticmethod
    def step_output_event(
        step_context: StepExecutionContext, step_output_data: StepOutputData
    ) -> "DagsterEvent":

        output_def = step_context.solid.output_def_named(
            step_output_data.step_output_handle.output_name
        )

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_OUTPUT,
            step_context=step_context,
            event_specific_data=step_output_data,
            message='Yielded output "{output_name}"{mapping_clause} of type "{output_type}".{type_check_clause}'.format(
                output_name=step_output_data.step_output_handle.output_name,
                output_type=output_def.dagster_type.display_name,
                type_check_clause=(
                    " Warning! Type check failed."
                    if not step_output_data.type_check_data.success
                    else " (Type check passed)."
                )
                if step_output_data.type_check_data
                else " (No type check).",
                mapping_clause=f' mapping key "{step_output_data.step_output_handle.mapping_key}"'
                if step_output_data.step_output_handle.mapping_key
                else "",
            ),
        )

    @staticmethod
    def step_failure_event(
        step_context: IStepContext,
        step_failure_data: "StepFailureData",
        message=None,
    ) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_FAILURE,
            step_context=step_context,
            event_specific_data=step_failure_data,
            message=(
                message
                or 'Execution of step "{step_key}" failed.'.format(step_key=step_context.step.key)
            ),
        )

    @staticmethod
    def step_retry_event(
        step_context: IStepContext, step_retry_data: "StepRetryData"
    ) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_UP_FOR_RETRY,
            step_context=step_context,
            event_specific_data=step_retry_data,
            message='Execution of step "{step_key}" failed and has requested a retry{wait_str}.'.format(
                step_key=step_context.step.key,
                wait_str=" in {n} seconds".format(n=step_retry_data.seconds_to_wait)
                if step_retry_data.seconds_to_wait
                else "",
            ),
        )

    @staticmethod
    def step_input_event(
        step_context: StepExecutionContext, step_input_data: "StepInputData"
    ) -> "DagsterEvent":
        input_def = step_context.solid_def.input_def_named(step_input_data.input_name)

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_INPUT,
            step_context=step_context,
            event_specific_data=step_input_data,
            message='Got input "{input_name}" of type "{input_type}".{type_check_clause}'.format(
                input_name=step_input_data.input_name,
                input_type=input_def.dagster_type.display_name,
                type_check_clause=(
                    " Warning! Type check failed."
                    if not step_input_data.type_check_data.success
                    else " (Type check passed)."
                )
                if step_input_data.type_check_data
                else " (No type check).",
            ),
        )

    @staticmethod
    def step_start_event(step_context: IStepContext) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_START,
            step_context=step_context,
            message='Started execution of step "{step_key}".'.format(
                step_key=step_context.step.key
            ),
        )

    @staticmethod
    def step_restarted_event(step_context: IStepContext, previous_attempts: int) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_RESTARTED,
            step_context=step_context,
            message='Started re-execution (attempt # {n}) of step "{step_key}".'.format(
                step_key=step_context.step.key, n=previous_attempts + 1
            ),
        )

    @staticmethod
    def step_success_event(
        step_context: IStepContext, success: "StepSuccessData"
    ) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SUCCESS,
            step_context=step_context,
            event_specific_data=success,
            message='Finished execution of step "{step_key}" in {duration}.'.format(
                step_key=step_context.step.key,
                duration=format_duration(success.duration_ms),
            ),
        )

    @staticmethod
    def step_skipped_event(step_context: IStepContext) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_SKIPPED,
            step_context=step_context,
            message='Skipped execution of step "{step_key}".'.format(
                step_key=step_context.step.key
            ),
        )

    @staticmethod
    def asset_materialization(
        step_context: IStepContext,
        materialization: Union[AssetMaterialization, Materialization],
        asset_lineage: Optional[List[AssetLineageInfo]] = None,
    ) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            step_context=step_context,
            event_specific_data=StepMaterializationData(materialization, asset_lineage),
            message=materialization.description
            if materialization.description
            else "Materialized value{label_clause}.".format(
                label_clause=" {label}".format(label=materialization.label)
                if materialization.label
                else ""
            ),
        )

    @staticmethod
    def asset_observation(
        step_context: IStepContext, observation: AssetObservation
    ) -> "DagsterEvent":
        return DagsterEvent.from_step(
            event_type=DagsterEventType.ASSET_OBSERVATION,
            step_context=step_context,
            event_specific_data=AssetObservationData(observation),
        )

    @staticmethod
    def step_expectation_result(
        step_context: IStepContext, expectation_result: ExpectationResult
    ) -> "DagsterEvent":
        def _msg():
            if expectation_result.description:
                return expectation_result.description

            return "Expectation{label_clause} {result_verb}".format(
                label_clause=" " + expectation_result.label if expectation_result.label else "",
                result_verb="passed" if expectation_result.success else "failed",
            )

        return DagsterEvent.from_step(
            event_type=DagsterEventType.STEP_EXPECTATION_RESULT,
            step_context=step_context,
            event_specific_data=StepExpectationResultData(expectation_result),
            message=_msg(),
        )

    @staticmethod
    def pipeline_start(pipeline_context: IPlanContext) -> "DagsterEvent":
        return DagsterEvent.from_pipeline(
            DagsterEventType.RUN_START,
            pipeline_context,
            message='Started execution of run for "{pipeline_name}".'.format(
                pipeline_name=pipeline_context.pipeline_name
            ),
        )

    @staticmethod
    def pipeline_success(pipeline_context: IPlanContext) -> "DagsterEvent":
        return DagsterEvent.from_pipeline(
            DagsterEventType.RUN_SUCCESS,
            pipeline_context,
            message='Finished execution of run for "{pipeline_name}".'.format(
                pipeline_name=pipeline_context.pipeline_name
            ),
        )

    @staticmethod
    def pipeline_failure(
        pipeline_context_or_name: Union[IPlanContext, str],
        context_msg: str,
        error_info: Optional[SerializableErrorInfo] = None,
    ) -> "DagsterEvent":
        check.str_param(context_msg, "context_msg")
        if isinstance(pipeline_context_or_name, IPlanContext):
            return DagsterEvent.from_pipeline(
                DagsterEventType.RUN_FAILURE,
                pipeline_context_or_name,
                message='Execution of run for "{pipeline_name}" failed. {context_msg}'.format(
                    pipeline_name=pipeline_context_or_name.pipeline_name,
                    context_msg=context_msg,
                ),
                event_specific_data=PipelineFailureData(error_info),
            )
        else:
            # when the failure happens trying to bring up context, the pipeline_context hasn't been
            # built and so can't use from_pipeline
            check.str_param(pipeline_context_or_name, "pipeline_name")
            event = DagsterEvent(
                event_type_value=DagsterEventType.RUN_FAILURE.value,
                pipeline_name=pipeline_context_or_name,
                event_specific_data=PipelineFailureData(error_info),
                message='Execution of run for "{pipeline_name}" failed. {context_msg}'.format(
                    pipeline_name=pipeline_context_or_name,
                    context_msg=context_msg,
                ),
                pid=os.getpid(),
            )
            return event

    @staticmethod
    def pipeline_canceled(
        pipeline_context: IPlanContext, error_info: Optional[SerializableErrorInfo] = None
    ) -> "DagsterEvent":
        return DagsterEvent.from_pipeline(
            DagsterEventType.RUN_CANCELED,
            pipeline_context,
            message='Execution of run for "{pipeline_name}" canceled.'.format(
                pipeline_name=pipeline_context.pipeline_name
            ),
            event_specific_data=PipelineCanceledData(
                check.opt_inst_param(error_info, "error_info", SerializableErrorInfo)
            ),
        )

    @staticmethod
    def step_worker_starting(
        step_context: IStepContext,
        message: str,
        metadata_entries: List[MetadataEntry],
    ) -> "DagsterEvent":
        return DagsterEvent.from_step(
            DagsterEventType.STEP_WORKER_STARTING,
            step_context,
            message=message,
            event_specific_data=EngineEventData(
                metadata_entries=metadata_entries, marker_start="step_process_start"
            ),
        )

    @staticmethod
    def step_worker_started(
        log_manager: DagsterLogManager,
        pipeline_name: str,
        message: str,
        metadata_entries: List[MetadataEntry],
        step_key: Optional[str],
    ) -> "DagsterEvent":
        event = DagsterEvent(
            DagsterEventType.STEP_WORKER_STARTED.value,
            pipeline_name=pipeline_name,
            message=message,
            event_specific_data=EngineEventData(
                metadata_entries=metadata_entries, marker_end="step_process_start"
            ),
            pid=os.getpid(),
            step_key=step_key,
        )
        log_manager.log_dagster_event(
            level=logging.DEBUG,
            msg=message,
            dagster_event=event,
        )
        return event

    @staticmethod
    def resource_init_start(
        pipeline_name: str,
        execution_plan: "ExecutionPlan",
        log_manager: DagsterLogManager,
        resource_keys: AbstractSet[str],
    ) -> "DagsterEvent":

        return DagsterEvent.from_resource(
            DagsterEventType.RESOURCE_INIT_STARTED,
            pipeline_name=pipeline_name,
            execution_plan=execution_plan,
            log_manager=log_manager,
            message="Starting initialization of resources [{}].".format(
                ", ".join(sorted(resource_keys))
            ),
            event_specific_data=EngineEventData(metadata_entries=[], marker_start="resources"),
        )

    @staticmethod
    def resource_init_success(
        pipeline_name: str,
        execution_plan: "ExecutionPlan",
        log_manager: DagsterLogManager,
        resource_instances: Dict[str, Any],
        resource_init_times: Dict[str, str],
    ) -> "DagsterEvent":

        metadata_entries = []
        for key in resource_instances.keys():
            metadata_entries.extend(
                [
                    MetadataEntry(
                        key,
                        value=MetadataValue.python_artifact(resource_instances[key].__class__),
                    ),
                    MetadataEntry(f"{key}:init_time", value=resource_init_times[key]),
                ]
            )

        return DagsterEvent.from_resource(
            DagsterEventType.RESOURCE_INIT_SUCCESS,
            pipeline_name=pipeline_name,
            execution_plan=execution_plan,
            log_manager=log_manager,
            message="Finished initialization of resources [{}].".format(
                ", ".join(sorted(resource_init_times.keys()))
            ),
            event_specific_data=EngineEventData(
                metadata_entries=metadata_entries,
                marker_end="resources",
            ),
        )

    @staticmethod
    def resource_init_failure(
        pipeline_name: str,
        execution_plan: "ExecutionPlan",
        log_manager: DagsterLogManager,
        resource_keys: AbstractSet[str],
        error: SerializableErrorInfo,
    ) -> "DagsterEvent":

        return DagsterEvent.from_resource(
            DagsterEventType.RESOURCE_INIT_FAILURE,
            pipeline_name=pipeline_name,
            execution_plan=execution_plan,
            log_manager=log_manager,
            message="Initialization of resources [{}] failed.".format(", ".join(resource_keys)),
            event_specific_data=EngineEventData(
                metadata_entries=[],
                marker_end="resources",
                error=error,
            ),
        )

    @staticmethod
    def resource_teardown_failure(
        pipeline_name: str,
        execution_plan: "ExecutionPlan",
        log_manager: DagsterLogManager,
        resource_keys: AbstractSet[str],
        error: SerializableErrorInfo,
    ) -> "DagsterEvent":

        return DagsterEvent.from_resource(
            DagsterEventType.ENGINE_EVENT,
            pipeline_name=pipeline_name,
            execution_plan=execution_plan,
            log_manager=log_manager,
            message="Teardown of resources [{}] failed.".format(", ".join(resource_keys)),
            event_specific_data=EngineEventData(
                metadata_entries=[],
                marker_start=None,
                marker_end=None,
                error=error,
            ),
        )

    @staticmethod
    def engine_event(
        plan_context: IPlanContext,
        message: str,
        event_specific_data: Optional["EngineEventData"] = None,
    ) -> "DagsterEvent":
        if isinstance(plan_context, IStepContext):
            return DagsterEvent.from_step(
                DagsterEventType.ENGINE_EVENT,
                step_context=plan_context,
                event_specific_data=event_specific_data,
                message=message,
            )
        else:
            return DagsterEvent.from_pipeline(
                DagsterEventType.ENGINE_EVENT,
                plan_context,
                message,
                event_specific_data=event_specific_data,
            )

    @staticmethod
    def object_store_operation(
        step_context: IStepContext, object_store_operation_result: "ObjectStoreOperation"
    ) -> "DagsterEvent":

        object_store_name = (
            "{object_store_name} ".format(
                object_store_name=object_store_operation_result.object_store_name
            )
            if object_store_operation_result.object_store_name
            else ""
        )

        serialization_strategy_modifier = (
            " using {serialization_strategy_name}".format(
                serialization_strategy_name=object_store_operation_result.serialization_strategy_name
            )
            if object_store_operation_result.serialization_strategy_name
            else ""
        )

        value_name = object_store_operation_result.value_name

        if (
            ObjectStoreOperationType(object_store_operation_result.op)
            == ObjectStoreOperationType.SET_OBJECT
        ):
            message = (
                "Stored intermediate object for output {value_name} in "
                "{object_store_name}object store{serialization_strategy_modifier}."
            ).format(
                value_name=value_name,
                object_store_name=object_store_name,
                serialization_strategy_modifier=serialization_strategy_modifier,
            )
        elif (
            ObjectStoreOperationType(object_store_operation_result.op)
            == ObjectStoreOperationType.GET_OBJECT
        ):
            message = (
                "Retrieved intermediate object for input {value_name} in "
                "{object_store_name}object store{serialization_strategy_modifier}."
            ).format(
                value_name=value_name,
                object_store_name=object_store_name,
                serialization_strategy_modifier=serialization_strategy_modifier,
            )
        elif (
            ObjectStoreOperationType(object_store_operation_result.op)
            == ObjectStoreOperationType.CP_OBJECT
        ):
            message = (
                "Copied intermediate object for input {value_name} from {key} to {dest_key}"
            ).format(
                value_name=value_name,
                key=object_store_operation_result.key,
                dest_key=object_store_operation_result.dest_key,
            )
        else:
            message = ""

        return DagsterEvent.from_step(
            DagsterEventType.OBJECT_STORE_OPERATION,
            step_context,
            event_specific_data=ObjectStoreOperationResultData(
                op=object_store_operation_result.op,
                value_name=value_name,
                address=object_store_operation_result.key,
                metadata_entries=[
                    MetadataEntry(
                        "key", value=MetadataValue.path(object_store_operation_result.key)
                    ),
                ],
                version=object_store_operation_result.version,
                mapping_key=object_store_operation_result.mapping_key,
            ),
            message=message,
        )

    @staticmethod
    def handled_output(
        step_context: IStepContext,
        output_name: str,
        manager_key: str,
        message_override: Optional[str] = None,
        metadata_entries: Optional[List[MetadataEntry]] = None,
    ) -> "DagsterEvent":
        message = f'Handled output "{output_name}" using IO manager "{manager_key}"'
        return DagsterEvent.from_step(
            event_type=DagsterEventType.HANDLED_OUTPUT,
            step_context=step_context,
            event_specific_data=HandledOutputData(
                output_name=output_name,
                manager_key=manager_key,
                metadata_entries=metadata_entries if metadata_entries else [],
            ),
            message=message_override or message,
        )

    @staticmethod
    def loaded_input(
        step_context: IStepContext,
        input_name: str,
        manager_key: str,
        upstream_output_name: Optional[str] = None,
        upstream_step_key: Optional[str] = None,
        message_override: Optional[str] = None,
        metadata_entries: Optional[List[MetadataEntry]] = None,
    ) -> "DagsterEvent":

        message = f'Loaded input "{input_name}" using input manager "{manager_key}"'
        if upstream_output_name:
            message += f', from output "{upstream_output_name}" of step ' f'"{upstream_step_key}"'

        return DagsterEvent.from_step(
            event_type=DagsterEventType.LOADED_INPUT,
            step_context=step_context,
            event_specific_data=LoadedInputData(
                input_name=input_name,
                manager_key=manager_key,
                upstream_output_name=upstream_output_name,
                upstream_step_key=upstream_step_key,
                metadata_entries=metadata_entries if metadata_entries else [],
            ),
            message=message_override or message,
        )

    @staticmethod
    def hook_completed(
        step_context: StepExecutionContext, hook_def: HookDefinition
    ) -> "DagsterEvent":
        event_type = DagsterEventType.HOOK_COMPLETED

        event = DagsterEvent(
            event_type_value=event_type.value,
            pipeline_name=step_context.pipeline_name,
            step_handle=step_context.step.handle,
            solid_handle=step_context.step.solid_handle,
            step_kind_value=step_context.step.kind.value,
            logging_tags=step_context.logging_tags,
            message=(
                'Finished the execution of hook "{hook_name}" triggered for "{solid_name}".'
            ).format(hook_name=hook_def.name, solid_name=step_context.solid.name),
        )

        step_context.log.log_dagster_event(
            level=logging.DEBUG, msg=event.message or "", dagster_event=event
        )

        return event

    @staticmethod
    def hook_errored(
        step_context: StepExecutionContext, error: HookExecutionError
    ) -> "DagsterEvent":
        event_type = DagsterEventType.HOOK_ERRORED

        event = DagsterEvent(
            event_type_value=event_type.value,
            pipeline_name=step_context.pipeline_name,
            step_handle=step_context.step.handle,
            solid_handle=step_context.step.solid_handle,
            step_kind_value=step_context.step.kind.value,
            logging_tags=step_context.logging_tags,
            event_specific_data=_validate_event_specific_data(
                event_type,
                HookErroredData(
                    error=serializable_error_info_from_exc_info(error.original_exc_info)
                ),
            ),
        )

        step_context.log.log_dagster_event(level=logging.ERROR, msg=str(error), dagster_event=event)

        return event

    @staticmethod
    def hook_skipped(
        step_context: StepExecutionContext, hook_def: HookDefinition
    ) -> "DagsterEvent":
        event_type = DagsterEventType.HOOK_SKIPPED

        event = DagsterEvent(
            event_type_value=event_type.value,
            pipeline_name=step_context.pipeline_name,
            step_handle=step_context.step.handle,
            solid_handle=step_context.step.solid_handle,
            step_kind_value=step_context.step.kind.value,
            logging_tags=step_context.logging_tags,
            message=(
                'Skipped the execution of hook "{hook_name}". It did not meet its triggering '
                'condition during the execution of "{solid_name}".'
            ).format(hook_name=hook_def.name, solid_name=step_context.solid.name),
        )

        step_context.log.log_dagster_event(
            level=logging.DEBUG, msg=event.message or "", dagster_event=event
        )

        return event

    @staticmethod
    def capture_logs(pipeline_context: IPlanContext, log_key: str, steps: List["ExecutionStep"]):
        step_keys = [step.key for step in steps]
        if len(step_keys) == 1:
            message = f"Started capturing logs for step: {step_keys[0]}."
        else:
            message = f"Started capturing logs in process (pid: {os.getpid()})."

        if isinstance(pipeline_context, StepExecutionContext):
            return DagsterEvent.from_step(
                DagsterEventType.LOGS_CAPTURED,
                pipeline_context,
                message=message,
                event_specific_data=ComputeLogsCaptureData(
                    step_keys=step_keys,
                    log_key=log_key,
                ),
            )

        return DagsterEvent.from_pipeline(
            DagsterEventType.LOGS_CAPTURED,
            pipeline_context,
            message=message,
            event_specific_data=ComputeLogsCaptureData(
                step_keys=step_keys,
                log_key=log_key,
            ),
        )


def get_step_output_event(
    events: List[DagsterEvent], step_key: str, output_name: Optional[str] = "result"
) -> Optional["DagsterEvent"]:
    check.list_param(events, "events", of_type=DagsterEvent)
    check.str_param(step_key, "step_key")
    check.str_param(output_name, "output_name")
    for event in events:
        if (
            event.event_type == DagsterEventType.STEP_OUTPUT
            and event.step_key == step_key
            and event.step_output_data.output_name == output_name
        ):
            return event
    return None


@whitelist_for_serdes
class AssetObservationData(
    NamedTuple("_AssetObservation", [("asset_observation", AssetObservation)])
):
    def __new__(cls, asset_observation: AssetObservation):
        return super(AssetObservationData, cls).__new__(
            cls,
            asset_observation=check.inst_param(
                asset_observation, "asset_observation", AssetObservation
            ),
        )


@whitelist_for_serdes
class StepMaterializationData(
    NamedTuple(
        "_StepMaterializationData",
        [
            ("materialization", Union[Materialization, AssetMaterialization]),
            ("asset_lineage", List[AssetLineageInfo]),
        ],
    )
):
    def __new__(
        cls,
        materialization: Union[Materialization, AssetMaterialization],
        asset_lineage: Optional[List[AssetLineageInfo]] = None,
    ):
        return super(StepMaterializationData, cls).__new__(
            cls,
            materialization=check.inst_param(
                materialization, "materialization", (Materialization, AssetMaterialization)
            ),
            asset_lineage=check.opt_list_param(
                asset_lineage, "asset_lineage", of_type=AssetLineageInfo
            ),
        )


@whitelist_for_serdes
class AssetMaterializationPlannedData(
    NamedTuple("_AssetMaterializationPlannedData", [("asset_key", AssetKey)])
):
    def __new__(cls, asset_key: AssetKey):
        return super(AssetMaterializationPlannedData, cls).__new__(
            cls, asset_key=check.inst_param(asset_key, "asset_key", AssetKey)
        )


@whitelist_for_serdes
class StepExpectationResultData(
    NamedTuple(
        "_StepExpectationResultData",
        [
            ("expectation_result", ExpectationResult),
        ],
    )
):
    def __new__(cls, expectation_result: ExpectationResult):
        return super(StepExpectationResultData, cls).__new__(
            cls,
            expectation_result=check.inst_param(
                expectation_result, "expectation_result", ExpectationResult
            ),
        )


@whitelist_for_serdes
class ObjectStoreOperationResultData(
    NamedTuple(
        "_ObjectStoreOperationResultData",
        [
            ("op", ObjectStoreOperationType),
            ("value_name", Optional[str]),
            ("metadata_entries", List[MetadataEntry]),
            ("address", Optional[str]),
            ("version", Optional[str]),
            ("mapping_key", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        op: ObjectStoreOperationType,
        value_name: Optional[str] = None,
        metadata_entries: Optional[List[MetadataEntry]] = None,
        address: Optional[str] = None,
        version: Optional[str] = None,
        mapping_key: Optional[str] = None,
    ):
        return super(ObjectStoreOperationResultData, cls).__new__(
            cls,
            op=cast(ObjectStoreOperationType, check.str_param(op, "op")),
            value_name=check.opt_str_param(value_name, "value_name"),
            metadata_entries=check.opt_list_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
            address=check.opt_str_param(address, "address"),
            version=check.opt_str_param(version, "version"),
            mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
        )


@whitelist_for_serdes
class EngineEventData(
    NamedTuple(
        "_EngineEventData",
        [
            ("metadata_entries", List[MetadataEntry]),
            ("error", Optional[SerializableErrorInfo]),
            ("marker_start", Optional[str]),
            ("marker_end", Optional[str]),
        ],
    )
):
    # serdes log
    # * added optional error
    # * added marker_start / marker_end
    #
    def __new__(
        cls,
        metadata_entries: Optional[List[MetadataEntry]] = None,
        error: Optional[SerializableErrorInfo] = None,
        marker_start: Optional[str] = None,
        marker_end: Optional[str] = None,
    ):
        return super(EngineEventData, cls).__new__(
            cls,
            metadata_entries=check.opt_list_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            marker_start=check.opt_str_param(marker_start, "marker_start"),
            marker_end=check.opt_str_param(marker_end, "marker_end"),
        )

    @staticmethod
    def in_process(pid: int, step_keys_to_execute: Optional[List[str]] = None) -> "EngineEventData":
        return EngineEventData(
            metadata_entries=[MetadataEntry("pid", value=str(pid))]
            + (
                [MetadataEntry("step_keys", value=str(step_keys_to_execute))]
                if step_keys_to_execute
                else []
            ),
        )

    @staticmethod
    def multiprocess(
        pid: int, step_keys_to_execute: Optional[List[str]] = None
    ) -> "EngineEventData":
        return EngineEventData(
            metadata_entries=[MetadataEntry("pid", value=str(pid))]
            + (
                [MetadataEntry("step_keys", value=str(step_keys_to_execute))]
                if step_keys_to_execute
                else []
            )
        )

    @staticmethod
    def interrupted(steps_interrupted: List[str]) -> "EngineEventData":
        return EngineEventData(
            metadata_entries=[MetadataEntry("steps_interrupted", value=str(steps_interrupted))]
        )

    @staticmethod
    def engine_error(error: SerializableErrorInfo) -> "EngineEventData":
        return EngineEventData(metadata_entries=[], error=error)


@whitelist_for_serdes
class PipelineFailureData(
    NamedTuple(
        "_PipelineFailureData",
        [
            ("error", Optional[SerializableErrorInfo]),
        ],
    )
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(PipelineFailureData, cls).__new__(
            cls, error=check.opt_inst_param(error, "error", SerializableErrorInfo)
        )


@whitelist_for_serdes
class PipelineCanceledData(
    NamedTuple(
        "_PipelineCanceledData",
        [
            ("error", Optional[SerializableErrorInfo]),
        ],
    )
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(PipelineCanceledData, cls).__new__(
            cls, error=check.opt_inst_param(error, "error", SerializableErrorInfo)
        )


@whitelist_for_serdes
class HookErroredData(
    NamedTuple(
        "_HookErroredData",
        [
            ("error", SerializableErrorInfo),
        ],
    )
):
    def __new__(cls, error: SerializableErrorInfo):
        return super(HookErroredData, cls).__new__(
            cls, error=check.inst_param(error, "error", SerializableErrorInfo)
        )


@whitelist_for_serdes
class HandledOutputData(
    NamedTuple(
        "_HandledOutputData",
        [
            ("output_name", str),
            ("manager_key", str),
            ("metadata_entries", List[MetadataEntry]),
        ],
    )
):
    def __new__(
        cls,
        output_name: str,
        manager_key: str,
        metadata_entries: Optional[List[MetadataEntry]] = None,
    ):
        return super(HandledOutputData, cls).__new__(
            cls,
            output_name=check.str_param(output_name, "output_name"),
            manager_key=check.str_param(manager_key, "manager_key"),
            metadata_entries=check.opt_list_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
        )


@whitelist_for_serdes
class LoadedInputData(
    NamedTuple(
        "_LoadedInputData",
        [
            ("input_name", str),
            ("manager_key", str),
            ("upstream_output_name", Optional[str]),
            ("upstream_step_key", Optional[str]),
            ("metadata_entries", Optional[List[MetadataEntry]]),
        ],
    )
):
    def __new__(
        cls,
        input_name: str,
        manager_key: str,
        upstream_output_name: Optional[str] = None,
        upstream_step_key: Optional[str] = None,
        metadata_entries: Optional[List[MetadataEntry]] = None,
    ):
        return super(LoadedInputData, cls).__new__(
            cls,
            input_name=check.str_param(input_name, "input_name"),
            manager_key=check.str_param(manager_key, "manager_key"),
            upstream_output_name=check.opt_str_param(upstream_output_name, "upstream_output_name"),
            upstream_step_key=check.opt_str_param(upstream_step_key, "upstream_step_key"),
            metadata_entries=check.opt_list_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
        )


@whitelist_for_serdes
class ComputeLogsCaptureData(
    NamedTuple(
        "_ComputeLogsCaptureData",
        [
            ("log_key", str),
            ("step_keys", List[str]),
        ],
    )
):
    def __new__(cls, log_key, step_keys):
        return super(ComputeLogsCaptureData, cls).__new__(
            cls,
            log_key=check.str_param(log_key, "log_key"),
            step_keys=check.opt_list_param(step_keys, "step_keys", of_type=str),
        )


###################################################################################################
# THE GRAVEYARD
#
#            -|-                  -|-                  -|-
#             |                    |                    |
#        _-'~~~~~`-_ .        _-'~~~~~`-_          _-'~~~~~`-_
#      .'           '.      .'           '.      .'           '.
#      |    R I P    |      |    R I P    |      |    R I P    |
#      |             |      |             |      |             |
#      |  Synthetic  |      |    Asset    |      |   Pipeline  |
#      |   Process   |      |    Store    |      |    Init     |
#      |   Events    |      |  Operations |      |   Failures  |
#      |             |      |             |      |             |
###################################################################################################

# Keep these around to prevent issues like https://github.com/dagster-io/dagster/issues/3533
@whitelist_for_serdes
class AssetStoreOperationData(NamedTuple):
    op: str
    step_key: str
    output_name: str
    asset_store_key: str


@whitelist_for_serdes
class AssetStoreOperationType(Enum):
    SET_ASSET = "SET_ASSET"
    GET_ASSET = "GET_ASSET"


@whitelist_for_serdes
class PipelineInitFailureData(NamedTuple):
    error: SerializableErrorInfo


def _handle_back_compat(event_type_value, event_specific_data):
    # transform old specific process events in to engine events
    if event_type_value == "PIPELINE_PROCESS_START":
        return DagsterEventType.ENGINE_EVENT.value, EngineEventData([])
    elif event_type_value == "PIPELINE_PROCESS_STARTED":
        return DagsterEventType.ENGINE_EVENT.value, EngineEventData([])
    elif event_type_value == "PIPELINE_PROCESS_EXITED":
        return DagsterEventType.ENGINE_EVENT.value, EngineEventData([])

    # changes asset store ops in to get/set asset
    elif event_type_value == "ASSET_STORE_OPERATION":
        if event_specific_data.op in ("GET_ASSET", AssetStoreOperationType.GET_ASSET):
            return (
                DagsterEventType.LOADED_INPUT.value,
                LoadedInputData(
                    event_specific_data.output_name, event_specific_data.asset_store_key
                ),
            )
        if event_specific_data.op in ("SET_ASSET", AssetStoreOperationType.SET_ASSET):
            return (
                DagsterEventType.HANDLED_OUTPUT.value,
                HandledOutputData(
                    event_specific_data.output_name, event_specific_data.asset_store_key, []
                ),
            )

    # previous name for ASSET_MATERIALIZATION was STEP_MATERIALIZATION
    if event_type_value == "STEP_MATERIALIZATION":
        return DagsterEventType.ASSET_MATERIALIZATION.value, event_specific_data

    # transform PIPELINE_INIT_FAILURE to PIPELINE_FAILURE
    if event_type_value == "PIPELINE_INIT_FAILURE":
        return DagsterEventType.PIPELINE_FAILURE.value, PipelineFailureData(
            event_specific_data.error
        )

    return event_type_value, event_specific_data


register_serdes_tuple_fallbacks(
    {
        "PipelineProcessStartedData": None,
        "PipelineProcessExitedData": None,
        "PipelineProcessStartData": None,
    }
)
