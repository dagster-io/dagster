from math import isnan

from dagster import check, seven
from dagster.core.definitions.events import (
    EventMetadataEntry,
    FloatMetadataEntryData,
    IntMetadataEntryData,
    JsonMetadataEntryData,
    MarkdownMetadataEntryData,
    PathMetadataEntryData,
    PythonArtifactMetadataEntryData,
    TextMetadataEntryData,
    UrlMetadataEntryData,
)
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.execution.plan.objects import StepFailureData


def iterate_metadata_entries(metadata_entries):
    from ..schema.logs.events import (
        GrapheneEventFloatMetadataEntry,
        GrapheneEventIntMetadataEntry,
        GrapheneEventJsonMetadataEntry,
        GrapheneEventMarkdownMetadataEntry,
        GrapheneEventPathMetadataEntry,
        GrapheneEventPythonArtifactMetadataEntry,
        GrapheneEventTextMetadataEntry,
        GrapheneEventUrlMetadataEntry,
    )

    check.list_param(metadata_entries, "metadata_entries", of_type=EventMetadataEntry)
    for metadata_entry in metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataEntryData):
            yield GrapheneEventPathMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                path=metadata_entry.entry_data.path,
            )
        elif isinstance(metadata_entry.entry_data, JsonMetadataEntryData):
            yield GrapheneEventJsonMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                jsonString=seven.json.dumps(metadata_entry.entry_data.data),
            )
        elif isinstance(metadata_entry.entry_data, TextMetadataEntryData):
            yield GrapheneEventTextMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                text=metadata_entry.entry_data.text,
            )
        elif isinstance(metadata_entry.entry_data, UrlMetadataEntryData):
            yield GrapheneEventUrlMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                url=metadata_entry.entry_data.url,
            )
        elif isinstance(metadata_entry.entry_data, MarkdownMetadataEntryData):
            yield GrapheneEventMarkdownMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                md_str=metadata_entry.entry_data.md_str,
            )
        elif isinstance(metadata_entry.entry_data, PythonArtifactMetadataEntryData):
            yield GrapheneEventPythonArtifactMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                module=metadata_entry.entry_data.module,
                name=metadata_entry.entry_data.name,
            )
        elif isinstance(metadata_entry.entry_data, FloatMetadataEntryData):
            float_val = metadata_entry.entry_data.value

            # coerce NaN to null
            if isnan(float_val):
                float_val = None

            yield GrapheneEventFloatMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                floatValue=float_val,
            )
        elif isinstance(metadata_entry.entry_data, IntMetadataEntryData):
            # coerce > 32 bit ints to null
            int_val = None
            if metadata_entry.entry_data.value.bit_length() <= 32:
                int_val = metadata_entry.entry_data.value

            yield GrapheneEventIntMetadataEntry(
                label=metadata_entry.label,
                description=metadata_entry.description,
                intValue=int_val,
                # make string representation available to allow for > 32bit int
                intRepr=str(metadata_entry.entry_data.value),
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
        GrapheneObjectStoreOperationEvent,
        GraphenePipelineCanceledEvent,
        GraphenePipelineCancelingEvent,
        GraphenePipelineDequeuedEvent,
        GraphenePipelineEnqueuedEvent,
        GraphenePipelineFailureEvent,
        GraphenePipelineInitFailureEvent,
        GraphenePipelineStartEvent,
        GraphenePipelineStartingEvent,
        GraphenePipelineSuccessEvent,
        GrapheneStepExpectationResultEvent,
        GrapheneStepMaterializationEvent,
    )

    # Lots of event types. Pylint thinks there are too many branches
    # pylint: disable=too-many-branches
    check.inst_param(event_record, "event_record", EventRecord)
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
        materialization = dagster_event.step_materialization_data.materialization
        asset_lineage = dagster_event.step_materialization_data.asset_lineage
        return GrapheneStepMaterializationEvent(
            materialization=materialization,
            assetLineage=asset_lineage,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = dagster_event.event_specific_data.expectation_result
        return GrapheneStepExpectationResultEvent(
            expectation_result=expectation_result, **basic_params
        )
    elif dagster_event.event_type == DagsterEventType.STEP_FAILURE:
        check.inst(dagster_event.step_failure_data, StepFailureData)
        return GrapheneExecutionStepFailureEvent(
            error=GraphenePythonError(dagster_event.step_failure_data.error),
            failureMetadata=dagster_event.step_failure_data.user_failure_data,
            errorSource=dagster_event.step_failure_data.error_source,
            **basic_params,
        )
    elif dagster_event.event_type == DagsterEventType.PIPELINE_ENQUEUED:
        return GraphenePipelineEnqueuedEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_DEQUEUED:
        return GraphenePipelineDequeuedEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_STARTING:
        return GraphenePipelineStartingEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_CANCELING:
        return GraphenePipelineCancelingEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_CANCELED:
        return GraphenePipelineCanceledEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_START:
        return GraphenePipelineStartEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS:
        return GraphenePipelineSuccessEvent(pipelineName=pipeline_name, **basic_params)
    elif dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE:
        return GraphenePipelineFailureEvent(
            pipelineName=pipeline_name,
            error=GraphenePythonError(dagster_event.pipeline_failure_data.error)
            if (dagster_event.pipeline_failure_data and dagster_event.pipeline_failure_data.error)
            else None,
            **basic_params,
        )

    elif dagster_event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE:
        return GraphenePipelineInitFailureEvent(
            pipelineName=pipeline_name,
            error=GraphenePythonError(dagster_event.pipeline_init_failure_data.error),
            **basic_params,
        )
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
    else:
        raise Exception(
            "Unknown DAGSTER_EVENT type {inner_type} found in logs".format(
                inner_type=dagster_event.event_type
            )
        )


def from_event_record(event_record, pipeline_name):
    from ..schema.logs.events import GrapheneLogMessageEvent

    check.inst_param(event_record, "event_record", EventRecord)
    check.str_param(pipeline_name, "pipeline_name")

    if event_record.is_dagster_event:
        return from_dagster_event_record(event_record, pipeline_name)
    else:
        return GrapheneLogMessageEvent(**construct_basic_params(event_record))


def construct_basic_params(event_record):
    from ..schema.logs.log_level import GrapheneLogLevel

    check.inst_param(event_record, "event_record", EventRecord)
    return {
        "runId": event_record.run_id,
        "message": event_record.dagster_event.message
        if (event_record.dagster_event and event_record.dagster_event.message)
        else event_record.user_message,
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
