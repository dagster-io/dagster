from dagster import DagsterInstance, ModeDefinition, PipelineDefinition, resource, solid
from dagster.core.events.log import EventRecord, construct_event_logger
from dagster.core.execution.api import (
    create_execution_plan,
    execute_pipeline_iterator,
    execute_plan_iterator,
    execute_run_iterator,
)
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.utils import make_new_run_id


@resource
def resource_a(context):
    context.log.info('CALLING A')
    yield 'A'
    context.log.info('CLEANING A')
    yield  # add the second yield here to test teardown generator exit handling


@resource
def resource_b(context):
    context.log.info('CALLING B')
    yield 'B'
    context.log.info('CLEANING B')
    yield  # add the second yield here to test teardown generator exit handling


@solid(required_resource_keys={'a', 'b'})
def resource_solid(_):
    return 'A'


def test_execute_pipeline_iterator():
    records = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        records.append(record)

    pipeline = PipelineDefinition(
        name='basic_resource_pipeline',
        solid_defs=[resource_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={'a': resource_a, 'b': resource_b},
                logger_defs={'callback': construct_event_logger(event_callback)},
            )
        ],
    )
    iterator = execute_pipeline_iterator(
        pipeline,
        environment_dict={'loggers': {'callback': {}}},
        instance=DagsterInstance.local_temp(),
    )

    event_type = None
    while event_type != 'STEP_START':
        event = next(iterator)
        event_type = event.event_type_value

    iterator.close()
    events = [record.dagster_event for record in records if record.is_dagster_event]
    messages = [record.user_message for record in records if not record.is_dagster_event]
    assert len([event for event in events if event.is_pipeline_failure]) > 0
    assert len([message for message in messages if message == 'CLEANING A']) > 0
    assert len([message for message in messages if message == 'CLEANING B']) > 0


def test_execute_run_iterator():
    records = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        records.append(record)

    instance = DagsterInstance.local_temp()

    pipeline = PipelineDefinition(
        name='basic_resource_pipeline',
        solid_defs=[resource_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={'a': resource_a, 'b': resource_b},
                logger_defs={'callback': construct_event_logger(event_callback)},
            )
        ],
    )
    pipeline_run = instance.create_run(
        PipelineRun(
            pipeline_name=pipeline.name,
            run_id=make_new_run_id(),
            environment_dict={'loggers': {'callback': {}}},
            mode='default',
            status=PipelineRunStatus.NOT_STARTED,
        )
    )

    iterator = execute_run_iterator(pipeline, pipeline_run, instance=instance)

    event_type = None
    while event_type != 'STEP_START':
        event = next(iterator)
        event_type = event.event_type_value

    iterator.close()
    events = [record.dagster_event for record in records if record.is_dagster_event]
    messages = [record.user_message for record in records if not record.is_dagster_event]
    assert len([event for event in events if event.is_pipeline_failure]) > 0
    assert len([message for message in messages if message == 'CLEANING A']) > 0
    assert len([message for message in messages if message == 'CLEANING B']) > 0


def test_execute_plan_iterator():
    records = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        records.append(record)

    instance = DagsterInstance.local_temp()

    pipeline = PipelineDefinition(
        name='basic_resource_pipeline',
        solid_defs=[resource_solid],
        mode_defs=[
            ModeDefinition(
                resource_defs={'a': resource_a, 'b': resource_b},
                logger_defs={'callback': construct_event_logger(event_callback)},
            )
        ],
    )
    environment_dict = {'loggers': {'callback': {}}}
    pipeline_run = instance.create_run(
        PipelineRun(
            pipeline_name=pipeline.name,
            run_id=make_new_run_id(),
            environment_dict={'loggers': {'callback': {}}},
            mode='default',
            status=PipelineRunStatus.NOT_STARTED,
        )
    )

    execution_plan = create_execution_plan(pipeline, environment_dict)
    iterator = execute_plan_iterator(
        execution_plan, pipeline_run, instance, environment_dict=environment_dict
    )

    event_type = None
    while event_type != 'STEP_START':
        event = next(iterator)
        event_type = event.event_type_value

    iterator.close()
    messages = [record.user_message for record in records if not record.is_dagster_event]
    assert len([message for message in messages if message == 'CLEANING A']) > 0
    assert len([message for message in messages if message == 'CLEANING B']) > 0
