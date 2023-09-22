from math import isnan
from typing import Any, Iterator, Mapping, Sequence, cast, no_type_check

import dagster._check as check
import dagster._seven as seven
from dagster import (
    BoolMetadataValue,
    DagsterAssetMetadataValue,
    FloatMetadataValue,
    IntMetadataValue,
    JsonMetadataValue,
    MarkdownMetadataValue,
    NotebookMetadataValue,
    NullMetadataValue,
    PathMetadataValue,
    PythonArtifactMetadataValue,
    TableMetadataValue,
    TableSchemaMetadataValue,
    TextMetadataValue,
    UrlMetadataValue,
)
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluationPlanned
from dagster._core.definitions.metadata import (
    DagsterRunMetadataValue,
    MetadataValue,
)
from dagster._core.events import (
    DagsterEventType,
    HandledOutputData,
    LoadedInputData,
    StepExpectationResultData,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.plan.inputs import StepInputData
from dagster._core.execution.plan.outputs import StepOutputData

MAX_INT = 2147483647
MIN_INT = -2147483648


def iterate_metadata_entries(metadata: Mapping[str, MetadataValue]) -> Iterator[Any]:
    from ..schema.metadata import (
        GrapheneAssetMetadataEntry,
        GrapheneBoolMetadataEntry,
        GrapheneFloatMetadataEntry,
        GrapheneIntMetadataEntry,
        GrapheneJsonMetadataEntry,
        GrapheneMarkdownMetadataEntry,
        GrapheneNotebookMetadataEntry,
        GrapheneNullMetadataEntry,
        GraphenePathMetadataEntry,
        GraphenePipelineRunMetadataEntry,
        GraphenePythonArtifactMetadataEntry,
        GrapheneTableMetadataEntry,
        GrapheneTableSchemaMetadataEntry,
        GrapheneTextMetadataEntry,
        GrapheneUrlMetadataEntry,
    )
    from ..schema.table import GrapheneTable, GrapheneTableSchema

    check.mapping_param(metadata, "metadata", key_type=str)
    for key, value in metadata.items():
        if isinstance(value, PathMetadataValue):
            yield GraphenePathMetadataEntry(
                label=key,
                path=value.path,
            )
        elif isinstance(value, NotebookMetadataValue):
            yield GrapheneNotebookMetadataEntry(
                label=key,
                path=value.path,
            )
        elif isinstance(value, JsonMetadataValue):
            yield GrapheneJsonMetadataEntry(
                label=key,
                jsonString=seven.json.dumps(value.data),
            )
        elif isinstance(value, TextMetadataValue):
            yield GrapheneTextMetadataEntry(
                label=key,
                text=value.text,
            )
        elif isinstance(value, UrlMetadataValue):
            yield GrapheneUrlMetadataEntry(
                label=key,
                url=value.url,
            )
        elif isinstance(value, MarkdownMetadataValue):
            yield GrapheneMarkdownMetadataEntry(
                label=key,
                md_str=value.md_str,
            )
        elif isinstance(value, PythonArtifactMetadataValue):
            yield GraphenePythonArtifactMetadataEntry(
                label=key,
                module=value.module,
                name=value.name,
            )
        elif isinstance(value, FloatMetadataValue):
            float_val = value.value

            # coerce NaN to null
            if float_val is not None and isnan(float_val):
                float_val = None

            yield GrapheneFloatMetadataEntry(
                label=key,
                floatValue=float_val,
            )
        elif isinstance(value, IntMetadataValue):
            # coerce > 32 bit ints to null
            int_val = None
            if isinstance(value.value, int) and MIN_INT <= value.value <= MAX_INT:
                int_val = value.value

            yield GrapheneIntMetadataEntry(
                label=key,
                intValue=int_val,
                # make string representation available to allow for > 32bit int
                intRepr=str(value.value),
            )
        elif isinstance(value, BoolMetadataValue):
            yield GrapheneBoolMetadataEntry(
                label=key,
                boolValue=value.value,
            )
        elif isinstance(value, NullMetadataValue):
            yield GrapheneNullMetadataEntry(
                label=key,
            )
        elif isinstance(value, DagsterRunMetadataValue):
            yield GraphenePipelineRunMetadataEntry(
                label=key,
                runId=value.run_id,
            )
        elif isinstance(value, DagsterAssetMetadataValue):
            yield GrapheneAssetMetadataEntry(
                label=key,
                assetKey=value.asset_key,
            )
        elif isinstance(value, TableMetadataValue):
            yield GrapheneTableMetadataEntry(
                label=key,
                table=GrapheneTable(
                    schema=value.schema,
                    records=[seven.json.dumps(record.data) for record in value.records],
                ),
            )
        elif isinstance(value, TableSchemaMetadataValue):
            yield GrapheneTableSchemaMetadataEntry(
                label=key,
                schema=GrapheneTableSchema(
                    constraints=value.schema.constraints,
                    columns=value.schema.columns,
                ),
            )
        else:
            # skip rest for now
            check.not_implemented(f"{type(value)} unsupported metadata entry for now")


def _to_metadata_entries(metadata: Mapping[str, MetadataValue]) -> Sequence[Any]:
    return list(iterate_metadata_entries(metadata or {}))


# We don't typecheck this due to the excessive number of type errors resulting from the
# non-type-checker legible relationship between `event_type` and the class of `event_specific_data`.
@no_type_check
def from_dagster_event_record(event_record: EventLogEntry, pipeline_name: str) -> Any:
    from ..schema.errors import GraphenePythonError
    from ..schema.logs.events import (
        GrapheneAlertFailureEvent,
        GrapheneAlertStartEvent,
        GrapheneAlertSuccessEvent,
        GrapheneAssetCheckEvaluationEvent,
        GrapheneAssetCheckEvaluationPlannedEvent,
        GrapheneAssetMaterializationPlannedEvent,
        GrapheneEngineEvent,
        GrapheneExecutionStepFailureEvent,
        GrapheneExecutionStepInputEvent,
        GrapheneExecutionStepOutputEvent,
        GrapheneExecutionStepRestartEvent,
        GrapheneExecutionStepSkippedEvent,
        GrapheneExecutionStepStartEvent,
        GrapheneExecutionStepSuccessEvent,
        GrapheneExecutionStepUpForRetryEvent,
        GrapheneHandledOutputEvent,
        GrapheneHookCompletedEvent,
        GrapheneHookErroredEvent,
        GrapheneHookSkippedEvent,
        GrapheneLoadedInputEvent,
        GrapheneLogsCapturedEvent,
        GrapheneMaterializationEvent,
        GrapheneObjectStoreOperationEvent,
        GrapheneObservationEvent,
        GrapheneResourceInitFailureEvent,
        GrapheneResourceInitStartedEvent,
        GrapheneResourceInitSuccessEvent,
        GrapheneRunCanceledEvent,
        GrapheneRunCancelingEvent,
        GrapheneRunDequeuedEvent,
        GrapheneRunEnqueuedEvent,
        GrapheneRunFailureEvent,
        GrapheneRunStartEvent,
        GrapheneRunStartingEvent,
        GrapheneRunSuccessEvent,
        GrapheneStepExpectationResultEvent,
        GrapheneStepWorkerStartedEvent,
        GrapheneStepWorkerStartingEvent,
    )

    # Lots of event types. Pylint thinks there are too many branches

    check.inst_param(event_record, "event_record", EventLogEntry)
    check.param_invariant(event_record.is_dagster_event, "event_record")
    check.str_param(pipeline_name, "pipeline_name")

    dagster_event = check.not_none(event_record.dagster_event)
    basic_params = construct_basic_params(event_record)
    if dagster_event.event_type == DagsterEventType.STEP_START:
        return GrapheneExecutionStepStartEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
        return GrapheneExecutionStepSkippedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_UP_FOR_RETRY:
        return GrapheneExecutionStepUpForRetryEvent(
            error=GraphenePythonError(dagster_event.step_retry_data.error),
            secondsToWait=dagster_event.step_retry_data.seconds_to_wait,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
        return GrapheneExecutionStepRestartEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
        return GrapheneExecutionStepSuccessEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_INPUT:
        data = cast(StepInputData, dagster_event.event_specific_data)
        return GrapheneExecutionStepInputEvent(
            input_name=data.input_name,
            type_check=data.type_check_data,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_OUTPUT:
        data = cast(StepOutputData, dagster_event.event_specific_data)
        return GrapheneExecutionStepOutputEvent(
            output_name=data.output_name,
            type_check=data.type_check_data,
            metadataEntries=_to_metadata_entries(data.metadata),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
        data = dagster_event.step_materialization_data
        return GrapheneMaterializationEvent(event=event_record, assetLineage=data.asset_lineage)
    elif dagster_event.event_type == DagsterEventType.ASSET_OBSERVATION:
        return GrapheneObservationEvent(
            event=event_record,
        )
    elif dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED:
        return GrapheneAssetMaterializationPlannedEvent(event=event_record)
    elif dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        data = cast(StepExpectationResultData, dagster_event.event_specific_data)
        return GrapheneStepExpectationResultEvent(
            expectation_result=data.expectation_result, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_FAILURE:
        data = dagster_event.step_failure_data
        return GrapheneExecutionStepFailureEvent(
            error=(GraphenePythonError(data.error) if data.error else None),
            failureMetadata=data.user_failure_data,
            errorSource=data.error_source,
            **basic_params,
        )

    elif dagster_event.event_type in (
        DagsterEventType.RUN_ENQUEUED,
        DagsterEventType.PIPELINE_ENQUEUED,
    ):
        return GrapheneRunEnqueuedEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_DEQUEUED,
        DagsterEventType.PIPELINE_DEQUEUED,
    ):
        return GrapheneRunDequeuedEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_STARTING,
        DagsterEventType.PIPELINE_STARTING,
    ):
        return GrapheneRunStartingEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_CANCELING,
        DagsterEventType.PIPELINE_CANCELING,
    ):
        return GrapheneRunCancelingEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_CANCELED,
        DagsterEventType.PIPELINE_CANCELED,
    ):
        return GrapheneRunCanceledEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_START,
        DagsterEventType.PIPELINE_START,
    ):
        return GrapheneRunStartEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_SUCCESS,
        DagsterEventType.PIPELINE_SUCCESS,
    ):
        return GrapheneRunSuccessEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type in (
        DagsterEventType.RUN_FAILURE,
        DagsterEventType.PIPELINE_FAILURE,
    ):
        data = dagster_event.job_failure_data
        return GrapheneRunFailureEvent(
            pipelineName=pipeline_name,
            error=GraphenePythonError(data.error) if (data and data.error) else None,
            **basic_params,
        )

    elif dagster_event.event_type == DagsterEventType.ALERT_START:
        return GrapheneAlertStartEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ALERT_SUCCESS:
        return GrapheneAlertSuccessEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ALERT_FAILURE:
        return GrapheneAlertFailureEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.HANDLED_OUTPUT:
        data = cast(HandledOutputData, dagster_event.event_specific_data)
        return GrapheneHandledOutputEvent(
            output_name=data.output_name,
            manager_key=data.manager_key,
            metadataEntries=_to_metadata_entries(
                dagster_event.event_specific_data.metadata  # type: ignore
            ),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.LOADED_INPUT:
        data = cast(LoadedInputData, dagster_event.event_specific_data)
        return GrapheneLoadedInputEvent(
            input_name=data.input_name,
            manager_key=data.manager_key,
            upstream_output_name=data.upstream_output_name,
            upstream_step_key=data.upstream_step_key,
            metadataEntries=_to_metadata_entries(data.metadata or {}),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.OBJECT_STORE_OPERATION:
        data = dagster_event.event_specific_data
        return GrapheneObjectStoreOperationEvent(operation_result=data, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ENGINE_EVENT:
        data = dagster_event.engine_event_data
        return GrapheneEngineEvent(
            metadataEntries=_to_metadata_entries(data.metadata),
            error=(
                GraphenePythonError(data.error) if dagster_event.engine_event_data.error else None
            ),
            markerStart=data.marker_start,
            markerEnd=data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.HOOK_COMPLETED:
        return GrapheneHookCompletedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.HOOK_SKIPPED:
        return GrapheneHookSkippedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.HOOK_ERRORED:
        data = dagster_event.hook_errored_data
        return GrapheneHookErroredEvent(
            error=GraphenePythonError(data.error),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.LOGS_CAPTURED:
        data = dagster_event.logs_captured_data
        return GrapheneLogsCapturedEvent(
            fileKey=data.file_key,
            logKey=data.file_key,
            stepKeys=data.step_keys,
            externalUrl=data.external_url,
            externalStdoutUrl=data.external_stdout_url or data.external_url,
            externalStderrUrl=data.external_stderr_url or data.external_url,
            pid=dagster_event.pid,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_WORKER_STARTING:
        data = dagster_event.engine_event_data
        return GrapheneStepWorkerStartingEvent(
            metadataEntries=_to_metadata_entries(data.metadata),
            markerStart=data.marker_start,
            markerEnd=data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_WORKER_STARTED:
        data = dagster_event.engine_event_data
        return GrapheneStepWorkerStartedEvent(
            metadataEntries=_to_metadata_entries(data.metadata),
            markerStart=data.marker_start,
            markerEnd=data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.RESOURCE_INIT_STARTED:
        data = dagster_event.engine_event_data
        return GrapheneResourceInitStartedEvent(
            metadataEntries=_to_metadata_entries(data.metadata),
            markerStart=data.marker_start,
            markerEnd=data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.RESOURCE_INIT_SUCCESS:
        data = dagster_event.engine_event_data
        return GrapheneResourceInitSuccessEvent(
            metadataEntries=_to_metadata_entries(data.metadata),
            markerStart=data.marker_start,
            markerEnd=data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.RESOURCE_INIT_FAILURE:
        data = dagster_event.engine_event_data
        return GrapheneResourceInitFailureEvent(
            metadataEntries=_to_metadata_entries(data.metadata),
            markerStart=data.marker_start,
            markerEnd=data.marker_end,
            error=GraphenePythonError(data.error),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED:
        data = cast(AssetCheckEvaluationPlanned, dagster_event.event_specific_data)
        return GrapheneAssetCheckEvaluationPlannedEvent(
            assetKey=data.asset_key, checkName=data.check_name, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION:
        from ..schema.asset_checks import GrapheneAssetCheckEvaluation

        evaluation = GrapheneAssetCheckEvaluation(event_record)
        return GrapheneAssetCheckEvaluationEvent(evaluation=evaluation, **basic_params)

    else:
        raise Exception(f"Unknown DAGSTER_EVENT type {dagster_event.event_type} found in logs")


def from_event_record(event_record: EventLogEntry, pipeline_name: str) -> Any:
    from ..schema.logs.events import GrapheneLogMessageEvent

    check.inst_param(event_record, "event_record", EventLogEntry)
    check.str_param(pipeline_name, "pipeline_name")

    if event_record.is_dagster_event:
        return from_dagster_event_record(event_record, pipeline_name)
    else:
        return GrapheneLogMessageEvent(**construct_basic_params(event_record))


def construct_basic_params(event_record: EventLogEntry) -> Any:
    from ..schema.logs.log_level import GrapheneLogLevel

    check.inst_param(event_record, "event_record", EventLogEntry)
    dagster_event = event_record.dagster_event
    return {
        "runId": event_record.run_id,
        "message": event_record.message,
        "timestamp": int(event_record.timestamp * 1000),
        "level": GrapheneLogLevel.from_level(event_record.level),
        "eventType": (
            dagster_event.event_type if (dagster_event and dagster_event.event_type) else None
        ),
        "stepKey": event_record.step_key,
        "solidHandleID": (
            event_record.dagster_event.node_handle.to_string()  # type: ignore
            if dagster_event and dagster_event.node_handle
            else None
        ),
    }
