from dagster_graphql.implementation.utils import ExecutionMetadata, ExecutionParams

from dagster import EventMetadataEntry, check, seven
from dagster.core.definitions import ExpectationResult, Materialization, SolidHandle
from dagster.core.definitions.events import PythonArtifactMetadataEntryData
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster.core.execution.plan.objects import (
    StepFailureData,
    StepInputData,
    StepOutputData,
    StepOutputHandle,
    StepRetryData,
    StepSuccessData,
    TypeCheckData,
    UserFailureData,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.utils import make_new_run_id
from dagster.utils.error import SerializableErrorInfo

HANDLED_EVENTS = {
    'ExecutionStepStartEvent': DagsterEventType.STEP_START,
    'ExecutionStepInputEvent': DagsterEventType.STEP_INPUT,
    'ExecutionStepOutputEvent': DagsterEventType.STEP_OUTPUT,
    'ExecutionStepFailureEvent': DagsterEventType.STEP_FAILURE,
    'ExecutionStepSkippedEvent': DagsterEventType.STEP_SKIPPED,
    'ExecutionStepSuccessEvent': DagsterEventType.STEP_SUCCESS,
    'StepMaterializationEvent': DagsterEventType.STEP_MATERIALIZATION,
    'StepExpectationResultEvent': DagsterEventType.STEP_EXPECTATION_RESULT,
    'ObjectStoreOperationEvent': DagsterEventType.OBJECT_STORE_OPERATION,
    'EngineEvent': DagsterEventType.ENGINE_EVENT,
    'ExecutionStepUpForRetryEvent': DagsterEventType.STEP_UP_FOR_RETRY,
    'ExecutionStepRestartEvent': DagsterEventType.STEP_RESTARTED,
}


def expectation_result_from_data(data):
    return ExpectationResult(
        success=data['success'],
        label=data['label'],
        description=data.get('description'),  # enforce?
        metadata_entries=list(event_metadata_entries(data.get('metadataEntries')) or []),
    )


def materialization_from_data(data):
    return Materialization(
        label=data['label'],
        description=data.get('description'),  # enforce?
        metadata_entries=list(event_metadata_entries(data.get('metadataEntries')) or []),
    )


def error_from_data(data):
    return SerializableErrorInfo(
        message=data['message'],
        stack=data['stack'],
        cls_name=data['className'],
        cause=error_from_data(data['cause']) if data.get('cause') else None,
    )


def event_metadata_entries(metadata_entry_datas):
    if not metadata_entry_datas:
        return

    for metadata_entry_data in metadata_entry_datas:
        typename = metadata_entry_data['__typename']
        label = metadata_entry_data['label']
        description = metadata_entry_data.get('description')
        if typename == 'EventPathMetadataEntry':
            yield EventMetadataEntry.path(
                label=label, description=description, path=metadata_entry_data['path']
            )
        elif typename == 'EventJsonMetadataEntry':
            yield EventMetadataEntry.json(
                label=label,
                description=description,
                data=seven.json.loads(metadata_entry_data.get('jsonString', '')),
            )
        elif typename == 'EventMarkdownMetadataEntry':
            yield EventMetadataEntry.md(
                label=label, description=description, md_str=metadata_entry_data.get('md_str', '')
            )
        elif typename == 'EventTextMetadataEntry':
            yield EventMetadataEntry.text(
                label=label, description=description, text=metadata_entry_data['text']
            )
        elif typename == 'EventUrlMetadataEntry':
            yield EventMetadataEntry.url(
                label=label, description=description, url=metadata_entry_data['url']
            )
        elif typename == 'EventPythonArtifactMetadataEntry':
            yield EventMetadataEntry(
                label=label,
                description=description,
                entry_data=PythonArtifactMetadataEntryData(
                    metadata_entry_data['module'], metadata_entry_data['name']
                ),
            )
        else:
            check.not_implemented('TODO for type {}'.format(typename))


def dagster_event_from_dict(event_dict, pipeline_name):
    check.dict_param(event_dict, 'event_dict', key_type=str)
    check.str_param(pipeline_name, 'pipeline_name')

    # Get event_type
    event_type = HANDLED_EVENTS.get(event_dict['__typename'])
    if not event_type:
        raise Exception('unhandled event type %s' % event_dict['__typename'])

    # Get event_specific_data
    event_specific_data = None
    if event_type == DagsterEventType.STEP_OUTPUT:
        event_specific_data = StepOutputData(
            step_output_handle=StepOutputHandle(
                event_dict['step']['key'], event_dict['outputName']
            ),
            type_check_data=TypeCheckData(
                success=event_dict['typeCheck']['success'],
                label=event_dict['typeCheck']['label'],
                description=event_dict.get('description'),
                metadata_entries=list(
                    event_metadata_entries(event_dict.get('metadataEntries')) or []
                ),
            ),
        )

    elif event_type == DagsterEventType.STEP_INPUT:
        event_specific_data = StepInputData(
            input_name=event_dict['inputName'],
            type_check_data=TypeCheckData(
                success=event_dict['typeCheck']['success'],
                label=event_dict['typeCheck']['label'],
                description=event_dict.get('description'),
                metadata_entries=list(
                    event_metadata_entries(event_dict.get('metadataEntries')) or []
                ),
            ),
        )
    elif event_type == DagsterEventType.STEP_SUCCESS:
        event_specific_data = StepSuccessData(0.0)

    elif event_type == DagsterEventType.STEP_UP_FOR_RETRY:
        event_specific_data = StepRetryData(
            error=error_from_data(event_dict['retryError']),
            seconds_to_wait=event_dict['secondsToWait'],
        )

    elif event_type == DagsterEventType.STEP_MATERIALIZATION:
        materialization = event_dict['materialization']
        event_specific_data = StepMaterializationData(
            materialization=materialization_from_data(materialization)
        )
    elif event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = expectation_result_from_data(event_dict['expectationResult'])
        event_specific_data = StepExpectationResultData(expectation_result)

    elif event_type == DagsterEventType.STEP_FAILURE:
        event_specific_data = StepFailureData(
            error_from_data(event_dict['error']),
            UserFailureData(
                label=event_dict['failureMetadata']['label'],
                description=event_dict['failureMetadata']['description'],
                metadata_entries=list(
                    event_metadata_entries(event_dict.get('metadataEntries')) or []
                ),
            )
            if event_dict.get('failureMetadata')
            else None,
        )

    elif event_type == DagsterEventType.ENGINE_EVENT:
        event_specific_data = EngineEventData(
            metadata_entries=list(event_metadata_entries(event_dict.get('metadataEntries'))),
            marker_start=event_dict.get('markerStart'),
            marker_end=event_dict.get('markerEnd'),
            error=error_from_data(event_dict['engineError'])
            if event_dict.get('engineError')
            else None,
        )

    # We should update the GraphQL response so that clients don't need to do this handle parsing.
    # See: https://github.com/dagster-io/dagster/issues/1559
    handle = None
    step_key = None
    step_kind_value = None
    if 'step' in event_dict and event_dict['step']:
        step_key = event_dict['step']['key']
        step_kind_value = event_dict['step']['kind']
        keys = event_dict['step']['solidHandleID'].split('.')
        while keys:
            handle = SolidHandle(keys.pop(0), definition_name=None, parent=handle)

    return DagsterEvent(
        event_type_value=event_type.value,
        pipeline_name=pipeline_name,
        step_key=step_key,
        solid_handle=handle,
        step_kind_value=step_kind_value,
        logging_tags=None,
        event_specific_data=event_specific_data,
    )


def pipeline_run_from_execution_params(execution_params, step_keys_to_execute=None):
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    return PipelineRun(
        pipeline_name=execution_params.selector.name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        selector=execution_params.selector,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
        step_keys_to_execute=step_keys_to_execute or execution_params.step_keys,
        tags=execution_params.execution_metadata.tags,
        status=PipelineRunStatus.NOT_STARTED,
        previous_run_id=execution_params.previous_run_id,
    )


def execution_params_from_pipeline_run(run):
    check.inst_param(run, 'run', PipelineRun)

    return ExecutionParams(
        mode=run.mode,
        step_keys=run.step_keys_to_execute,
        environment_dict=run.environment_dict,
        selector=run.selector,
        execution_metadata=ExecutionMetadata(run_id=run.run_id, tags=run.tags),
        previous_run_id=run.previous_run_id,
    )
