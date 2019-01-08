from collections import defaultdict

from dagster import (
    ExecutionContext,
    PipelineDefinition,
    PipelineContextDefinition,
    execute_pipeline,
    lambda_solid,
)

from dagster.core.events import construct_event_logger, EventRecord, EventType

from dagster.utils.logging import define_colored_console_logger


def single_event(events, event_type):
    assert event_type in events
    assert len(events[event_type]) == 1
    return events[event_type][0]


def define_event_logging_pipeline(name, solids, event_callback, deps=None):
    return PipelineDefinition(
        name=name,
        solids=solids,
        description=deps,
        context_definitions={
            'default': PipelineContextDefinition(
                context_fn=lambda info: ExecutionContext(
                    loggers=[
                        construct_event_logger(event_callback),
                        define_colored_console_logger('yup'),
                    ]
                )
            )
        },
    )


def test_empty_pipeline():
    events = defaultdict(list)

    def _event_callback(record):
        assert isinstance(record, EventRecord)
        events[record.event_type].append(record)

    pipeline_def = define_event_logging_pipeline(
        name='empty_pipeline', solids=[], event_callback=_event_callback
    )

    result = execute_pipeline(pipeline_def)
    assert result.success
    assert events

    assert single_event(events, EventType.PIPELINE_START).pipeline_name == 'empty_pipeline'
    assert single_event(events, EventType.PIPELINE_SUCCESS).pipeline_name == 'empty_pipeline'


def test_single_solid_pipeline_success():
    events = defaultdict(list)

    @lambda_solid
    def solid_one():
        return 1

    def _event_callback(record):
        events[record.event_type].append(record)

    pipeline_def = define_event_logging_pipeline(
        name='single_solid_pipeline', solids=[solid_one], event_callback=_event_callback
    )

    result = execute_pipeline(pipeline_def)
    assert result.success
    assert events

    start_event = single_event(events, EventType.EXECUTION_PLAN_STEP_START)
    assert start_event.pipeline_name == 'single_solid_pipeline'
    assert start_event.solid_name == 'solid_one'

    assert start_event.solid_definition_name == 'solid_one'
    success_event = single_event(events, EventType.EXECUTION_PLAN_STEP_SUCCESS)
    assert success_event.pipeline_name == 'single_solid_pipeline'
    assert success_event.solid_name == 'solid_one'
    assert success_event.solid_definition_name == 'solid_one'

    assert isinstance(success_event.millis, float)
    assert success_event.millis > 0.0


def test_single_solid_pipeline_failure():
    events = defaultdict(list)

    @lambda_solid
    def solid_one():
        raise Exception('nope')

    def _event_callback(record):
        events[record.event_type].append(record)

    pipeline_def = define_event_logging_pipeline(
        name='single_solid_pipeline', solids=[solid_one], event_callback=_event_callback
    )

    result = execute_pipeline(pipeline_def, throw_on_error=False)
    assert not result.success

    start_event = single_event(events, EventType.EXECUTION_PLAN_STEP_START)
    assert start_event.pipeline_name == 'single_solid_pipeline'
    assert start_event.solid_name == 'solid_one'
    assert start_event.solid_definition_name == 'solid_one'

    failure_event = single_event(events, EventType.EXECUTION_PLAN_STEP_FAILURE)
    assert failure_event.pipeline_name == 'single_solid_pipeline'
    assert failure_event.solid_name == 'solid_one'
    assert failure_event.solid_definition_name == 'solid_one'
