from .logging import EventType, EventRecord, PipelineEventRecord
from dagster import check


def get_step_output_event(events, step_key, output_name='result'):
    from .execution import ExecutionStepEvent, ExecutionStepEventType

    check.list_param(events, 'events', of_type=ExecutionStepEvent)
    check.str_param(step_key, 'step_key')
    check.str_param(output_name, 'output_name')
    for event in events:
        if (
            event.event_type == ExecutionStepEventType.STEP_OUTPUT
            and event.step_key == step_key
            and event.step_output_data.output_name == output_name
        ):
            return event
    return None
