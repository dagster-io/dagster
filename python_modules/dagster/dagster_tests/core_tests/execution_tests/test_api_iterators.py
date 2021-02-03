import pytest
from dagster import ModeDefinition, PipelineDefinition, check, resource, solid
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events.log import EventRecord, construct_event_logger
from dagster.core.execution.api import (
    create_execution_plan,
    execute_pipeline_iterator,
    execute_plan_iterator,
    execute_run,
    execute_run_iterator,
)
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test


@resource
def resource_a(context):
    context.log.info("CALLING A")
    yield "A"
    context.log.info("CLEANING A")
    yield  # add the second yield here to test teardown generator exit handling


@resource
def resource_b(context):
    context.log.info("CALLING B")
    yield "B"
    context.log.info("CLEANING B")
    yield  # add the second yield here to test teardown generator exit handling


@solid(required_resource_keys={"a", "b"})
def resource_solid(_):
    return "A"


def test_execute_pipeline_iterator():
    with instance_for_test() as instance:
        records = []

        def event_callback(record):
            assert isinstance(record, EventRecord)
            records.append(record)

        pipeline = PipelineDefinition(
            name="basic_resource_pipeline",
            solid_defs=[resource_solid],
            mode_defs=[
                ModeDefinition(
                    resource_defs={"a": resource_a, "b": resource_b},
                    logger_defs={"callback": construct_event_logger(event_callback)},
                )
            ],
        )
        iterator = execute_pipeline_iterator(
            pipeline, run_config={"loggers": {"callback": {}}}, instance=instance
        )

        event_type = None
        while event_type != "STEP_START":
            event = next(iterator)
            event_type = event.event_type_value

        iterator.close()
        events = [record.dagster_event for record in records if record.is_dagster_event]
        messages = [record.user_message for record in records if not record.is_dagster_event]
        pipeline_failure_events = [event for event in events if event.is_pipeline_failure]
        assert len(pipeline_failure_events) == 1
        assert "GeneratorExit" in pipeline_failure_events[0].pipeline_failure_data.error.message
        assert len([message for message in messages if message == "CLEANING A"]) > 0
        assert len([message for message in messages if message == "CLEANING B"]) > 0


def test_execute_run_iterator():
    records = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        records.append(record)

    with instance_for_test() as instance:
        pipeline_def = PipelineDefinition(
            name="basic_resource_pipeline",
            solid_defs=[resource_solid],
            mode_defs=[
                ModeDefinition(
                    resource_defs={"a": resource_a, "b": resource_b},
                    logger_defs={"callback": construct_event_logger(event_callback)},
                )
            ],
        )
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config={"loggers": {"callback": {}}},
            mode="default",
        )

        iterator = execute_run_iterator(
            InMemoryPipeline(pipeline_def), pipeline_run, instance=instance
        )

        event_type = None
        while event_type != "STEP_START":
            event = next(iterator)
            event_type = event.event_type_value

        iterator.close()
        events = [record.dagster_event for record in records if record.is_dagster_event]
        messages = [record.user_message for record in records if not record.is_dagster_event]
        pipeline_failure_events = [event for event in events if event.is_pipeline_failure]
        assert len(pipeline_failure_events) == 1
        assert "GeneratorExit" in pipeline_failure_events[0].pipeline_failure_data.error.message
        assert len([message for message in messages if message == "CLEANING A"]) > 0
        assert len([message for message in messages if message == "CLEANING B"]) > 0

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config={"loggers": {"callback": {}}},
            mode="default",
        ).with_status(PipelineRunStatus.SUCCESS)

        with pytest.raises(
            check.CheckError,
            match=r"Pipeline run basic_resource_pipeline \({}\) in state"
            r" PipelineRunStatus.SUCCESS, expected NOT_STARTED or STARTING".format(
                pipeline_run.run_id
            ),
        ):
            execute_run_iterator(InMemoryPipeline(pipeline_def), pipeline_run, instance=instance)

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config={"loggers": {"callback": {}}},
            mode="default",
        ).with_status(PipelineRunStatus.CANCELED)

        events = list(
            execute_run_iterator(InMemoryPipeline(pipeline_def), pipeline_run, instance=instance)
        )

        assert len(events) == 1
        assert (
            events[0].message
            == "Not starting execution since the run was canceled before execution could start"
        )


def test_execute_canceled_state():
    def event_callback(_record):
        pass

    with instance_for_test() as instance:
        pipeline_def = PipelineDefinition(
            name="basic_resource_pipeline",
            solid_defs=[resource_solid],
            mode_defs=[
                ModeDefinition(
                    resource_defs={"a": resource_a, "b": resource_b},
                    logger_defs={"callback": construct_event_logger(event_callback)},
                )
            ],
        )
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config={"loggers": {"callback": {}}},
            mode="default",
        ).with_status(PipelineRunStatus.CANCELED)

        with pytest.raises(DagsterInvariantViolationError):
            execute_run(
                InMemoryPipeline(pipeline_def),
                pipeline_run,
                instance=instance,
            )

        logs = instance.all_logs(pipeline_run.run_id)

        assert len(logs) == 1
        assert (
            "Not starting execution since the run was canceled before execution could start"
            in logs[0].message
        )

        iter_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config={"loggers": {"callback": {}}},
            mode="default",
        ).with_status(PipelineRunStatus.CANCELED)

        iter_events = list(
            execute_run_iterator(InMemoryPipeline(pipeline_def), iter_run, instance=instance)
        )

        assert len(iter_events) == 1
        assert (
            "Not starting execution since the run was canceled before execution could start"
            in iter_events[0].message
        )


def test_execute_run_bad_state():
    records = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        records.append(record)

    with instance_for_test() as instance:
        pipeline_def = PipelineDefinition(
            name="basic_resource_pipeline",
            solid_defs=[resource_solid],
            mode_defs=[
                ModeDefinition(
                    resource_defs={"a": resource_a, "b": resource_b},
                    logger_defs={"callback": construct_event_logger(event_callback)},
                )
            ],
        )
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            run_config={"loggers": {"callback": {}}},
            mode="default",
        ).with_status(PipelineRunStatus.SUCCESS)

        with pytest.raises(
            check.CheckError,
            match=r"Pipeline run basic_resource_pipeline \({}\) in state"
            r" PipelineRunStatus.SUCCESS, expected NOT_STARTED or STARTING".format(
                pipeline_run.run_id
            ),
        ):
            execute_run(InMemoryPipeline(pipeline_def), pipeline_run, instance=instance)


def test_execute_plan_iterator():
    records = []

    def event_callback(record):
        assert isinstance(record, EventRecord)
        records.append(record)

    with instance_for_test() as instance:
        pipeline = PipelineDefinition(
            name="basic_resource_pipeline",
            solid_defs=[resource_solid],
            mode_defs=[
                ModeDefinition(
                    resource_defs={"a": resource_a, "b": resource_b},
                    logger_defs={"callback": construct_event_logger(event_callback)},
                )
            ],
        )
        run_config = {"loggers": {"callback": {}}}

        execution_plan = create_execution_plan(pipeline, run_config=run_config)
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline,
            run_config={"loggers": {"callback": {}}},
            execution_plan=execution_plan,
        )

        iterator = execute_plan_iterator(
            execution_plan, pipeline_run, instance, run_config=run_config
        )

        event_type = None
        while event_type != "STEP_START":
            event = next(iterator)
            event_type = event.event_type_value

        iterator.close()
        messages = [record.user_message for record in records if not record.is_dagster_event]
        assert len([message for message in messages if message == "CLEANING A"]) > 0
        assert len([message for message in messages if message == "CLEANING B"]) > 0
