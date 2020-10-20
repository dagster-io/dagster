import pytest
from dagster import DagsterInstance, check, pipeline, solid
from dagster.core.errors import (
    DagsterIncompleteExecutionPlanError,
    DagsterInvalidConfigError,
    DagsterUnknownStepStateError,
)
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.retries import Retries, RetryMode

from ..engine_tests.test_multiprocessing import define_diamond_pipeline


def test_topological_sort():
    plan = create_execution_plan(define_diamond_pipeline())

    levels = plan.topological_step_levels()

    assert len(levels) == 3

    assert [step.key for step in levels[0]] == ["return_two.compute"]
    assert [step.key for step in levels[1]] == ["add_three.compute", "mult_three.compute"]
    assert [step.key for step in levels[2]] == ["adder.compute"]


def test_create_execution_plan_with_bad_inputs():
    with pytest.raises(DagsterInvalidConfigError):
        create_execution_plan(
            define_diamond_pipeline(), run_config={"solids": {"add_three": {"inputs": {"num": 3}}}},
        )


def test_active_execution_plan():
    plan = create_execution_plan(define_diamond_pipeline())

    with plan.start(retries=Retries(RetryMode.DISABLED)) as active_execution:

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_1 = steps[0]
        assert step_1.key == "return_two.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 2
        step_2 = steps[0]
        step_3 = steps[1]
        assert step_2.key == "add_three.compute"
        assert step_3.key == "mult_three.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_2.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_3.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_4 = steps[0]

        assert step_4.key == "adder.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        assert not active_execution.is_complete

        active_execution.mark_success(step_4.key)

        assert active_execution.is_complete


def test_failing_execution_plan():
    pipeline_def = define_diamond_pipeline()
    plan = create_execution_plan(pipeline_def)

    with plan.start(retries=Retries(RetryMode.DISABLED)) as active_execution:

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_1 = steps[0]
        assert step_1.key == "return_two.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 2
        step_2 = steps[0]
        step_3 = steps[1]
        assert step_2.key == "add_three.compute"
        assert step_3.key == "mult_three.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_2.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        # uh oh failure
        active_execution.mark_failed(step_3.key)

        # cant progres to 4th step
        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0

        assert not active_execution.is_complete

        steps = active_execution.get_steps_to_abandon()
        assert len(steps) == 1
        step_4 = steps[0]

        assert step_4.key == "adder.compute"
        active_execution.mark_abandoned(step_4.key)

        assert active_execution.is_complete


def test_retries_active_execution():
    pipeline_def = define_diamond_pipeline()
    plan = create_execution_plan(pipeline_def)

    with plan.start(retries=Retries(RetryMode.ENABLED)) as active_execution:

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_1 = steps[0]
        assert step_1.key == "return_two.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_up_for_retry(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        assert steps[0].key == "return_two.compute"

        active_execution.mark_up_for_retry(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        assert steps[0].key == "return_two.compute"

        active_execution.mark_success(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 2
        step_2 = steps[0]
        step_3 = steps[1]
        assert step_2.key == "add_three.compute"
        assert step_3.key == "mult_three.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_2.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        # uh oh failure
        active_execution.mark_failed(step_3.key)

        # cant progres to 4th step
        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0

        assert not active_execution.is_complete

        steps = active_execution.get_steps_to_abandon()
        assert len(steps) == 1
        step_4 = steps[0]

        assert step_4.key == "adder.compute"
        active_execution.mark_abandoned(step_4.key)

        assert active_execution.is_complete


def test_retries_disabled_active_execution():
    pipeline_def = define_diamond_pipeline()
    plan = create_execution_plan(pipeline_def)

    with pytest.raises(check.CheckError):
        with plan.start(retries=Retries(RetryMode.DISABLED)) as active_execution:

            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            assert step_1.key == "return_two.compute"

            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 0  # cant progress

            # raises
            active_execution.mark_up_for_retry(step_1.key)


def test_retries_deferred_active_execution():
    pipeline_def = define_diamond_pipeline()
    plan = create_execution_plan(pipeline_def)

    with plan.start(retries=Retries(RetryMode.DEFERRED)) as active_execution:

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_1 = steps[0]
        assert step_1.key == "return_two.compute"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_up_for_retry(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress, retries are deferred

        assert not active_execution.is_complete

        steps = active_execution.get_steps_to_abandon()
        # skip split of diamond
        assert len(steps) == 2
        _ = [active_execution.mark_abandoned(step.key) for step in steps]

        assert not active_execution.is_complete

        steps = active_execution.get_steps_to_abandon()
        # skip end of diamond
        assert len(steps) == 1
        active_execution.mark_abandoned(steps[0].key)

        assert active_execution.is_complete


def test_priorities():
    @solid(tags={"priority": 5})
    def pri_5(_):
        pass

    @solid(tags={"priority": 4})
    def pri_4(_):
        pass

    @solid(tags={"priority": 3})
    def pri_3(_):
        pass

    @solid(tags={"priority": 2})
    def pri_2(_):
        pass

    @solid(tags={"priority": -1})
    def pri_neg_1(_):
        pass

    @solid
    def pri_none(_):
        pass

    @pipeline
    def priorities():
        pri_neg_1()
        pri_3()
        pri_2()
        pri_none()
        pri_5()
        pri_4()

    sort_key_fn = lambda step: int(step.tags.get("priority", 0)) * -1

    plan = create_execution_plan(priorities)
    with plan.start(Retries(RetryMode.DISABLED), sort_key_fn) as active_execution:
        steps = active_execution.get_steps_to_execute()
        assert steps[0].key == "pri_5.compute"
        assert steps[1].key == "pri_4.compute"
        assert steps[2].key == "pri_3.compute"
        assert steps[3].key == "pri_2.compute"
        assert steps[4].key == "pri_none.compute"
        assert steps[5].key == "pri_neg_1.compute"
        _ = [active_execution.mark_skipped(step.key) for step in steps]


def test_executor_not_created_for_execute_plan():
    instance = DagsterInstance.ephemeral()
    pipe = define_diamond_pipeline()
    plan = create_execution_plan(pipe)
    pipeline_run = instance.create_run_for_pipeline(pipe, plan)

    results = execute_plan(
        plan, instance, pipeline_run, run_config={"execution": {"multiprocess": {}}}
    )
    for result in results:
        assert not result.is_failure


def test_incomplete_execution_plan():
    plan = create_execution_plan(define_diamond_pipeline())

    with pytest.raises(DagsterIncompleteExecutionPlanError):
        with plan.start(retries=Retries(RetryMode.DISABLED)) as active_execution:

            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            active_execution.mark_success(step_1.key)

            # exit early


def test_lost_steps():
    plan = create_execution_plan(define_diamond_pipeline())

    # run to completion - but step was in unknown state so exception thrown
    with pytest.raises(DagsterUnknownStepStateError):
        with plan.start(retries=Retries(RetryMode.DISABLED)) as active_execution:

            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]

            # called by verify_complete when success / fail event not observed
            active_execution.mark_unknown_state(step_1.key)

            # failure assumed for start step - so rest should skip
            steps_to_abandon = active_execution.get_steps_to_abandon()
            while steps_to_abandon:
                _ = [active_execution.mark_abandoned(step.key) for step in steps_to_abandon]
                steps_to_abandon = active_execution.get_steps_to_abandon()

            assert active_execution.is_complete
