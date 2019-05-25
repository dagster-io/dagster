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
    StepOutputData,
    StepOutputHandle,
    StepSuccessData,
)
from dagster.utils.error import SerializableErrorInfo

# Fragment for exhaustively retrieving all properties of step events
GraphQLFragment = namedtuple('_StepEventFragment', 'include_key fragment')


def get_step_event_fragment():
    return GraphQLFragment(
        include_key='...stepEventFragment',
        fragment='''
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
      name
      message
      resultMetadataJsonString
    }
  }
  ... on StepMaterializationEvent {
    materialization {
      description
      path
    }
  }
  ... on ExecutionStepOutputEvent {
    outputName
    valueRepr
    intermediateMaterialization {
      description
      path
    }
  }
  ... on ExecutionStepFailureEvent {
    error {
      message
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
        'ExecutionStepOutputEvent': DagsterEventType.STEP_OUTPUT,
        'ExecutionStepFailureEvent': DagsterEventType.STEP_FAILURE,
        'ExecutionStepSkippedEvent': DagsterEventType.STEP_SKIPPED,
        'ExecutionStepSuccessEvent': DagsterEventType.STEP_SUCCESS,
        'StepMaterializationEvent': DagsterEventType.STEP_MATERIALIZATION,
        'StepExpectationResultEvent': DagsterEventType.STEP_EXPECTATION_RESULT,
    }


def dagster_event_from_dict(event_dict, pipeline_name):
    check.dict_param(event_dict, 'event_dict', key_type=str)
    check.str_param(pipeline_name, 'pipeline_name')

    materialization = event_dict.get('intermediateMaterialization') or {}

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
            value_repr=event_dict['valueRepr'],
            intermediate_materialization=Materialization(
                path=materialization.get('path'), description=materialization.get('description')
            ),
        )

    elif event_type == DagsterEventType.STEP_SUCCESS:
        event_specific_data = StepSuccessData(0.0)

    elif event_type == DagsterEventType.STEP_MATERIALIZATION:
        event_specific_data = StepMaterializationData(
            materialization=Materialization(
                path=materialization.get('path'), description=materialization.get('description')
            )
        )
    elif event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
        result_metadata = event_dict['expectationResult']['resultMetadataJsonString']
        expectation_result = ExpectationResult(
            event_dict['expectationResult']['success'],
            event_dict['expectationResult']['name'],
            event_dict['expectationResult']['message'],
            json.loads(result_metadata) if result_metadata else None,
        )
        event_specific_data = StepExpectationResultData(expectation_result)

    elif event_type == DagsterEventType.STEP_FAILURE:
        error_info = SerializableErrorInfo(
            event_dict['error']['message'], stack=None, cls_name=None
        )
        event_specific_data = StepFailureData(error_info)

    return DagsterEvent(
        event_type_value=event_type.value,
        pipeline_name=pipeline_name,
        step_key=event_dict['step']['key'],
        solid_handle=SolidHandle(event_dict['step']['solidHandleID'], None, None),
        step_kind_value=event_dict['step']['kind'],
        logging_tags=None,
        event_specific_data=event_specific_data,
    )
