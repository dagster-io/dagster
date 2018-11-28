from collections import defaultdict

from dagster import (
    ExecutionContext,
    PipelineDefinition,
    PipelineContextDefinition,
    execute_pipeline,
)

from dagster.core.events import (
    construct_event_logger,
    EventRecord,
    EventType,
)


def single_event(events, event_type):
    assert event_type in events
    assert len(events[event_type]) == 1
    return events[event_type][0]


def test_empty_pipeline():
    events = defaultdict(list)

    def _event_callback(record):
        assert isinstance(record, EventRecord)

        events[record.event_type].append(record)

    pipeline_def = PipelineDefinition(
        name='empty_pipeline',
        solids=[],
        context_definitions={
            'default':
            PipelineContextDefinition(
                context_fn=
                lambda info: ExecutionContext(loggers=[construct_event_logger(_event_callback)])
            )
        }
    )

    result = execute_pipeline(pipeline_def)
    assert result.success
    assert events

    assert single_event(events, EventType.PIPELINE_START).pipeline_name == 'empty_pipeline'
    assert single_event(events, EventType.PIPELINE_SUCCESS).pipeline_name == 'empty_pipeline'
