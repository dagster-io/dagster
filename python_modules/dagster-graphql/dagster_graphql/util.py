import json

from collections import namedtuple

from dagster import check

from dagster.core.definitions import ExpectationResult, Materialization, SolidHandle

from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    StepExpectationResultData,
    StepMaterializationData,
)
from dagster.core.execution.plan.objects import (
    StepFailureData,
    StepInputData,
    StepOutputData,
    StepOutputHandle,
    StepSuccessData,
    TypeCheckData,
    UserFailureData,
)
from dagster.utils.error import SerializableErrorInfo

# Fragment for exhaustively retrieving all properties of step events
GraphQLFragment = namedtuple('_StepEventFragment', 'include_key fragment')


def get_step_event_fragment():
    return GraphQLFragment(
        include_key='...stepEventFragment',
        fragment='''
fragment eventMetadataEntryFragment on EventMetadataEntry {
  __typename
  label
  description
  ... on EventPathMetadataEntry {
      path
  }
  ... on EventJsonMetadataEntry {
      jsonString
  }
}

fragment stepEventFragment on StepEvent {
  step {
    key
    inputs {
      name
      type {
        key
      }
      dependsOn {
        key
      }
    }
    outputs {
      name
      type {
        key
      }
    }
    solidHandleID
    kind
    metadata {
      key
      value
    }
  }
  ... on MessageEvent {
    runId
    message
    timestamp
    level
  }
  ... on StepExpectationResultEvent {
    expectationResult {
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on StepMaterializationEvent {
    materialization {
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepInputEvent {
    inputName
    typeCheck {
      __typename
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepOutputEvent {
    outputName
    typeCheck {
      __typename
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepFailureEvent {
    error {
      message
    }
    failureMetadata {
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
}
'''.strip(),
    )


def get_log_message_event_fragment():
    return GraphQLFragment(
        include_key='...logMessageEventFragment',
        fragment='''
fragment logMessageEventFragment on LogMessageEvent {
  runId
  message
  timestamp
  level
  step {
    key
    inputs {
      name
      type {
        key
      }
      dependsOn {
        key
      }
    }
    outputs {
      name
      type {
        key
      }
    }
    solidHandleID
    kind
    metadata {
      key
      value
    }
  }
}
  ''',
    )


def _handled_events():
    return {
        'ExecutionStepStartEvent': DagsterEventType.STEP_START,
        'ExecutionStepInputEvent': DagsterEventType.STEP_INPUT,
        'ExecutionStepOutputEvent': DagsterEventType.STEP_OUTPUT,
        'ExecutionStepFailureEvent': DagsterEventType.STEP_FAILURE,
        'ExecutionStepSkippedEvent': DagsterEventType.STEP_SKIPPED,
        'ExecutionStepSuccessEvent': DagsterEventType.STEP_SUCCESS,
        'StepMaterializationEvent': DagsterEventType.STEP_MATERIALIZATION,
        'StepExpectationResultEvent': DagsterEventType.STEP_EXPECTATION_RESULT,
    }


from dagster import EventMetadataEntry


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
                data=json.loads(metadata_entry_data.get('jsonString', '')),
            )
        else:
            check.not_implemented('TODO for type {}'.format(typename))


def dagster_event_from_dict(event_dict, pipeline_name):
    check.dict_param(event_dict, 'event_dict', key_type=str)
    check.str_param(pipeline_name, 'pipeline_name')

    # Get event_type
    event_type = _handled_events().get(event_dict['__typename'])
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

    elif event_type == DagsterEventType.STEP_MATERIALIZATION:
        materialization = event_dict['materialization']
        event_specific_data = StepMaterializationData(
            materialization=materialization_from_data(materialization)
        )
    elif event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        expectation_result = expectation_result_from_data(event_dict['expectationResult'])
        event_specific_data = StepExpectationResultData(expectation_result)

    elif event_type == DagsterEventType.STEP_FAILURE:
        error_info = SerializableErrorInfo(
            event_dict['error']['message'], stack=None, cls_name=None
        )
        event_specific_data = StepFailureData(
            error_info,
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

    # We should update the GraphQL response so that clients don't need to do this handle parsing.
    # See: https://github.com/dagster-io/dagster/issues/1559
    keys = event_dict['step']['solidHandleID'].split('.')
    handle = None
    while keys:
        handle = SolidHandle(keys.pop(0), definition_name=None, parent=handle)

    return DagsterEvent(
        event_type_value=event_type.value,
        pipeline_name=pipeline_name,
        step_key=event_dict['step']['key'],
        solid_handle=handle,
        step_kind_value=event_dict['step']['kind'],
        logging_tags=None,
        event_specific_data=event_specific_data,
    )
