from math import isnan

from dagster_graphql.schema.table import GrapheneTable, GrapheneTableSchema

import dagster._check as check
import dagster.seven as seven
from dagster.core.definitions.metadata import (
    BoolMetadataValue,
    DagsterAssetMetadataValue,
    DagsterPipelineRunMetadataValue,
    FloatMetadataValue,
    IntMetadataValue,
    JsonMetadataValue,
    MarkdownMetadataValue,
    MetadataEntry,
    PathMetadataValue,
    PythonArtifactMetadataValue,
    TableMetadataValue,
    TableSchemaMetadataValue,
    TextMetadataValue,
    UrlMetadataValue,
)
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.plan.objects import StepFailureData

MAX_INT = 2147483647
MIN_INT = -2147483648


def iterate_metadata_entries(metadata_entries):
    from ..schema.metadata import (
        GrapheneAssetMetadataEntry,
        GrapheneBoolMetadataEntry,
        GrapheneFloatMetadataEntry,
        GrapheneIntMetadataEntry,
        GrapheneJsonMetadataEntry,
        GrapheneMarkdownMetadataEntry,
        GraphenePathMetadataEntry,
        GraphenePipelineRunMetadataEntry,
        GraphenePythonArtifactMetadataEntry,
        GrapheneTableMetadataEntry,
        GrapheneTableSchemaMetadataEntry,
        GrapheneTextMetadataEntry,
        GrapheneUrlMetadataEntry,
    )

    check.list_param(metadata_entries, "metadata_entries", of_type=MetadataEntry)
    for metadata_entry in metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataValue):
            yield GraphenePathMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                path=metadata_entry.entry_data.path,
            )
        elif isinstance(metadata_entry.entry_data, JsonMetadataValue):
            yield GrapheneJsonMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                jsonString=seven.json.dumps(metadata_entry.entry_data.data),
            )
        elif isinstance(metadata_entry.entry_data, TextMetadataValue):
            yield GrapheneTextMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                text=metadata_entry.entry_data.text,
            )
        elif isinstance(metadata_entry.entry_data, UrlMetadataValue):
            yield GrapheneUrlMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                url=metadata_entry.entry_data.url,
            )
        elif isinstance(metadata_entry.entry_data, MarkdownMetadataValue):
            yield GrapheneMarkdownMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                md_str=metadata_entry.entry_data.md_str,
            )
        elif isinstance(metadata_entry.entry_data, PythonArtifactMetadataValue):
            yield GraphenePythonArtifactMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                module=metadata_entry.entry_data.module,
                name=metadata_entry.entry_data.name,
            )
        elif isinstance(metadata_entry.entry_data, FloatMetadataValue):
            float_val = metadata_entry.entry_data.value

            # coerce NaN to null
            if isnan(float_val):
                float_val = None

            yield GrapheneFloatMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                floatValue=float_val,
            )
        elif isinstance(metadata_entry.entry_data, IntMetadataValue):
            # coerce > 32 bit ints to null
            int_val = None
            if MIN_INT <= metadata_entry.entry_data.value <= MAX_INT:
                int_val = metadata_entry.entry_data.value

            yield GrapheneIntMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                intValue=int_val,
                # make string representation available to allow for > 32bit int
                intRepr=str(metadata_entry.entry_data.value),
            )
        elif isinstance(metadata_entry.entry_data, BoolMetadataValue):
            yield GrapheneBoolMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                boolValue=metadata_entry.entry_data.value,
            )
        elif isinstance(metadata_entry.entry_data, DagsterPipelineRunMetadataValue):
            yield GraphenePipelineRunMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                runId=metadata_entry.entry_data.run_id,
            )
        elif isinstance(metadata_entry.entry_data, DagsterAssetMetadataValue):
            yield GrapheneAssetMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                assetKey=metadata_entry.entry_data.asset_key,
            )
        elif isinstance(metadata_entry.entry_data, TableMetadataValue):
            yield GrapheneTableMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                table=GrapheneTable(
                    schema=metadata_entry.entry_data.schema,
                    records=[
                        seven.json.dumps(record.data)
                        for record in metadata_entry.entry_data.records
                    ],
                ),
            )
        elif isinstance(metadata_entry.entry_data, TableSchemaMetadataValue):
            yield GrapheneTableSchemaMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                schema=GrapheneTableSchema(
                    constraints=metadata_entry.entry_data.schema.constraints,
                    columns=metadata_entry.entry_data.schema.columns,
                ),
            )
        else:
            # skip rest for now
            check.not_implemented(
                "{} unsupported metadata entry for now".format(type(metadata_entry.entry_data))
            )


def _to_metadata_entries(metadata_entries):
    return list(iterate_metadata_entries(metadata_entries) or [])


def from_dagster_event_record(event_record, pipeline_name):
    from ..schema.errors import GraphenePythonError
    from ..schema.logs.events import (
        GrapheneAlertFailureEvent,
        GrapheneAlertStartEvent,
        GrapheneAlertSuccessEvent,
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
        GrapheneRunCanceledEvent,
        GrapheneRunCancelingEvent,
        GrapheneRunDequeuedEvent,
        GrapheneRunEnqueuedEvent,
        GrapheneRunFailureEvent,
        GrapheneRunStartEvent,
        GrapheneRunStartingEvent,
        GrapheneRunSuccessEvent,
        GrapheneStepExpectationResultEvent,
    )

    # Lots of event types. Pylint thinks there are too many branches
    # pylint: disable=too-many-branches
    check.inst_param(event_record, "event_record", EventLogEntry)
    check.param_invariant(event_record.is_dagster_event, "event_record")
    check.str_param(pipeline_name, "pipeline_name")

    dagster_event = event_record.dagster_event
    basic_params = construct_basic_params(event_record)
    if dagster_event.event_type == DagsterEventType.STEP_START:
        return GrapheneExecutionStepStartEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
        return GrapheneExecutionStepSkippedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_UP_FOR_RETRY:
        return GrapheneExecutionStepUpForRetryEvent(
            error=dagster_event.step_retry_data.error,
            secondsToWait=dagster_event.step_retry_data.seconds_to_wait,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
        return GrapheneExecutionStepRestartEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
        return GrapheneExecutionStepSuccessEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.STEP_INPUT:
        input_data = dagster_event.event_specific_data
        return GrapheneExecutionStepInputEvent(
            input_name=input_data.input_name, type_check=input_data.type_check_data, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_OUTPUT:
        output_data = dagster_event.step_output_data
        return GrapheneExecutionStepOutputEvent(
            output_name=output_data.output_name,
            type_check=output_data.type_check_data,
            metadataEntries=_to_metadata_entries(output_data.metadata_entries),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
        asset_lineage = dagster_event.step_materialization_data.asset_lineage
        return GrapheneMaterializationEvent(event=event_record, assetLineage=asset_lineage)
    elif dagster_event.event_type == DagsterEventType.ASSET_OBSERVATION:
        return GrapheneObservationEvent(
            event=event_record,
        )
    elif dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED:
        return GrapheneAssetMaterializationPlannedEvent(event=event_record)
    elif dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = dagster_event.event_specific_data.expectation_result
        return GrapheneStepExpectationResultEvent(
            expectation_result=expectation_result, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_FAILURE:
        check.inst(dagster_event.step_failure_data, StepFailureData)
        return GrapheneExecutionStepFailureEvent(
            error=(
                GraphenePythonError(dagster_event.step_failure_data.error)
                if dagster_event.step_failure_data.error
                else None
            ),
            failureMetadata=dagster_event.step_failure_data.user_failure_data,
            errorSource=dagster_event.step_failure_data.error_source,
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
    elif dagster_event.event_type in (DagsterEventType.RUN_START, DagsterEventType.PIPELINE_START):
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
        return GrapheneRunFailureEvent(
            pipelineName=pipeline_name,
            error=GraphenePythonError(dagster_event.pipeline_failure_data.error)
            if (dagster_event.pipeline_failure_data and dagster_event.pipeline_failure_data.error)
            else None,
            **basic_params,
        )

    elif dagster_event.event_type == DagsterEventType.ALERT_START:
        return GrapheneAlertStartEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ALERT_SUCCESS:
        return GrapheneAlertSuccessEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ALERT_FAILURE:
        return GrapheneAlertFailureEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.HANDLED_OUTPUT:
        return GrapheneHandledOutputEvent(
            output_name=dagster_event.event_specific_data.output_name,
            manager_key=dagster_event.event_specific_data.manager_key,
            metadataEntries=_to_metadata_entries(
                dagster_event.event_specific_data.metadata_entries
            ),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.LOADED_INPUT:
        return GrapheneLoadedInputEvent(
            input_name=dagster_event.event_specific_data.input_name,
            manager_key=dagster_event.event_specific_data.manager_key,
            upstream_output_name=dagster_event.event_specific_data.upstream_output_name,
            upstream_step_key=dagster_event.event_specific_data.upstream_step_key,
            metadataEntries=_to_metadata_entries(
                dagster_event.event_specific_data.metadata_entries
            ),
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.OBJECT_STORE_OPERATION:
        operation_result = dagster_event.event_specific_data
        return GrapheneObjectStoreOperationEvent(operation_result=operation_result, **basic_params)
    elif dagster_event.event_type == DagsterEventType.ENGINE_EVENT:
        return GrapheneEngineEvent(
            metadataEntries=_to_metadata_entries(dagster_event.engine_event_data.metadata_entries),
            error=GraphenePythonError(dagster_event.engine_event_data.error)
            if dagster_event.engine_event_data.error
            else None,
            marker_start=dagster_event.engine_event_data.marker_start,
            marker_end=dagster_event.engine_event_data.marker_end,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.HOOK_COMPLETED:
        return GrapheneHookCompletedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.HOOK_SKIPPED:
        return GrapheneHookSkippedEvent(**basic_params)
    elif dagster_event.event_type == DagsterEventType.HOOK_ERRORED:
        return GrapheneHookErroredEvent(
            error=GraphenePythonError(dagster_event.hook_errored_data.error), **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.LOGS_CAPTURED:
        return GrapheneLogsCapturedEvent(
            logKey=dagster_event.logs_captured_data.log_key,
            stepKeys=dagster_event.logs_captured_data.step_keys,
            pid=dagster_event.pid,
            **basic_params,
        )
    else:
        raise Exception(
            "Unknown DAGSTER_EVENT type {inner_type} found in logs".format(
                inner_type=dagster_event.event_type
            )
        )


def from_event_record(event_record, pipeline_name):
    from ..schema.logs.events import GrapheneLogMessageEvent

    check.inst_param(event_record, "event_record", EventLogEntry)
    check.str_param(pipeline_name, "pipeline_name")

    if event_record.is_dagster_event:
        return from_dagster_event_record(event_record, pipeline_name)
    else:
        return GrapheneLogMessageEvent(**construct_basic_params(event_record))


def construct_basic_params(event_record):
    from ..schema.logs.log_level import GrapheneLogLevel

    check.inst_param(event_record, "event_record", EventLogEntry)
    return {
        "runId": event_record.run_id,
        "message": event_record.message,
        "timestamp": int(event_record.timestamp * 1000),
        "level": GrapheneLogLevel.from_level(event_record.level),
        "eventType": event_record.dagster_event.event_type
        if (event_record.dagster_event and event_record.dagster_event.event_type)
        else None,
        "stepKey": event_record.step_key,
        "solidHandleID": event_record.dagster_event.solid_handle.to_string()
        if event_record.is_dagster_event and event_record.dagster_event.solid_handle
        else None,
    }
