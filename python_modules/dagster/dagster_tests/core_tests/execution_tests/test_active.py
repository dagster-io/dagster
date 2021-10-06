from dagster import solid, pipeline
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.plan.objects import StepSuccessData
from dagster.core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster.core.execution.retries import RetryMode
from dagster.core.execution.api import create_execution_plan
import pytest


def define_foo_pipeline():
    @solid
    def foo_solid():
        pass

    @pipeline
    def foo_pipeline():
        foo_solid()

    return foo_pipeline


def test_recover_with_step_in_flight():
    foo_pipeline = define_foo_pipeline()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Execution finished without completing the execution plan",
    ):
        with create_execution_plan(foo_pipeline).start(RetryMode.DISABLED) as active_execution:
            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            assert step_1.key == "foo_solid"

            active_execution.handle_event(
                DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    pipeline_name=foo_pipeline.name,
                    step_key=step_1.key,
                )
            )

    # CRASH! Now we recover

    with create_execution_plan(foo_pipeline).start(RetryMode.DISABLED) as active_execution:
        possibly_in_flight_steps = active_execution.rebuild_from_events(
            [
                DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    pipeline_name=foo_pipeline.name,
                    step_key=step_1.key,
                )
            ]
        )
        assert possibly_in_flight_steps == [step_1]

        assert not active_execution.get_steps_to_execute()

        active_execution.handle_event(
            DagsterEvent(
                DagsterEventType.STEP_SUCCESS.value,
                pipeline_name=foo_pipeline.name,
                event_specific_data=StepSuccessData(duration_ms=10.0),
                step_key=step_1.key,
            )
        )


def define_two_solid_pipeline():
    @solid
    def foo_solid():
        pass

    @solid
    def bar_solid(_data):
        pass

    @pipeline
    def two_solid_pipeline():
        bar_solid(foo_solid())

    return two_solid_pipeline


def test_recover_in_between_steps():
    two_solid_pipeline = define_two_solid_pipeline()

    events = [
        DagsterEvent(
            DagsterEventType.STEP_START.value,
            pipeline_name=two_solid_pipeline.name,
            step_key="foo_solid",
        ),
        DagsterEvent(
            DagsterEventType.STEP_OUTPUT.value,
            pipeline_name=two_solid_pipeline.name,
            event_specific_data=StepOutputData(
                StepOutputHandle(step_key="foo_solid", output_name="result")
            ),
            step_key="foo_solid",
        ),
        DagsterEvent(
            DagsterEventType.STEP_SUCCESS.value,
            pipeline_name=two_solid_pipeline.name,
            event_specific_data=StepSuccessData(duration_ms=10.0),
            step_key="foo_solid",
        ),
    ]

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Execution finished without completing the execution plan",
    ):
        with create_execution_plan(two_solid_pipeline).start(
            RetryMode.DISABLED
        ) as active_execution:
            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            assert step_1.key == "foo_solid"

            active_execution.handle_event(events[0])
            active_execution.handle_event(events[1])
            active_execution.handle_event(events[2])

    # CRASH! Now we recover

    with create_execution_plan(two_solid_pipeline).start(RetryMode.DISABLED) as active_execution:
        possibly_in_flight_steps = active_execution.rebuild_from_events(events)
        assert len(possibly_in_flight_steps) == 1
        step_2 = possibly_in_flight_steps[0]
        assert step_2.key == "bar_solid"

        assert not active_execution.get_steps_to_execute()

        active_execution.handle_event(
            DagsterEvent(
                DagsterEventType.STEP_START.value,
                pipeline_name=two_solid_pipeline.name,
                step_key="bar_solid",
            )
        )
        active_execution.handle_event(
            DagsterEvent(
                DagsterEventType.STEP_SUCCESS.value,
                pipeline_name=two_solid_pipeline.name,
                event_specific_data=StepSuccessData(duration_ms=10.0),
                step_key="bar_solid",
            )
        )
