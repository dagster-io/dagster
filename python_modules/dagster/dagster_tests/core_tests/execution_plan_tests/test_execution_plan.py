import pytest
from dagster import (
    DagsterInstance,
    Int,
    Output,
    OutputDefinition,
    check,
    composite_solid,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.core.errors import (
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    DagsterUnknownStepStateError,
)
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.plan import should_skip_step
from dagster.core.execution.retries import Retries, RetryMode
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.utils import make_new_run_id

from ..engine_tests.test_multiprocessing import define_diamond_pipeline


def test_topological_sort():
    plan = create_execution_plan(define_diamond_pipeline())

    levels = plan.get_steps_to_execute_by_level()

    assert len(levels) == 3

    assert [step.key for step in levels[0]] == ["return_two"]
    assert [step.key for step in levels[1]] == ["add_three", "mult_three"]
    assert [step.key for step in levels[2]] == ["adder"]


def test_create_execution_plan_with_bad_inputs():
    with pytest.raises(DagsterInvalidConfigError):
        create_execution_plan(
            define_diamond_pipeline(),
            run_config={"solids": {"add_three": {"inputs": {"num": 3}}}},
        )


def test_active_execution_plan():
    plan = create_execution_plan(define_diamond_pipeline())

    with plan.start(retries=Retries(RetryMode.DISABLED)) as active_execution:

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_1 = steps[0]
        assert step_1.key == "return_two"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_1.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_1.key, "result"))

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 2
        step_2 = steps[0]
        step_3 = steps[1]
        assert step_2.key == "add_three"
        assert step_3.key == "mult_three"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_2.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_2.key, "result"))

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_3.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_3.key, "result"))

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_4 = steps[0]

        assert step_4.key == "adder"

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
        assert step_1.key == "return_two"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_1.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_1.key, "result"))

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 2
        step_2 = steps[0]
        step_3 = steps[1]
        assert step_2.key == "add_three"
        assert step_3.key == "mult_three"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_2.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_2.key, "result"))

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        # uh oh failure
        active_execution.mark_failed(step_3.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_3.key, "result"))

        # cant progres to 4th step
        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0

        assert not active_execution.is_complete

        steps = active_execution.get_steps_to_abandon()
        assert len(steps) == 1
        step_4 = steps[0]

        assert step_4.key == "adder"
        active_execution.mark_abandoned(step_4.key)

        assert active_execution.is_complete


def test_retries_active_execution():
    pipeline_def = define_diamond_pipeline()
    plan = create_execution_plan(pipeline_def)

    with plan.start(retries=Retries(RetryMode.ENABLED)) as active_execution:

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        step_1 = steps[0]
        assert step_1.key == "return_two"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_up_for_retry(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        assert steps[0].key == "return_two"

        active_execution.mark_up_for_retry(step_1.key)

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 1
        assert steps[0].key == "return_two"

        active_execution.mark_success(step_1.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_1.key, "result"))

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 2
        step_2 = steps[0]
        step_3 = steps[1]
        assert step_2.key == "add_three"
        assert step_3.key == "mult_three"

        steps = active_execution.get_steps_to_execute()
        assert len(steps) == 0  # cant progress

        active_execution.mark_success(step_2.key)
        active_execution.mark_step_produced_output(StepOutputHandle(step_2.key, "result"))

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

        assert step_4.key == "adder"
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
            assert step_1.key == "return_two"

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
        assert step_1.key == "return_two"

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
        assert steps[0].key == "pri_5"
        assert steps[1].key == "pri_4"
        assert steps[2].key == "pri_3"
        assert steps[3].key == "pri_2"
        assert steps[4].key == "pri_none"
        assert steps[5].key == "pri_neg_1"
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

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Execution of pipeline finished without completing the execution plan.",
    ):
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


def test_fan_out_should_skip_step():
    @solid(
        output_defs=[
            OutputDefinition(Int, "out_1", is_required=False),
            OutputDefinition(Int, "out_2", is_required=False),
            OutputDefinition(Int, "out_3", is_required=False),
        ]
    )
    def foo(_):
        yield Output(1, "out_1")

    @solid
    def bar(_, input_arg):
        return input_arg

    @pipeline
    def optional_outputs():
        foo_res = foo()
        # pylint: disable=no-member
        bar.alias("bar_1")(input_arg=foo_res.out_1)
        bar.alias("bar_2")(input_arg=foo_res.out_2)
        bar.alias("bar_3")(input_arg=foo_res.out_3)

    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(pipeline_name="optional_outputs", run_id=make_new_run_id())
    execute_plan(
        create_execution_plan(optional_outputs, step_keys_to_execute=["foo"]),
        instance,
        pipeline_run,
    )

    assert not should_skip_step(
        create_execution_plan(optional_outputs, step_keys_to_execute=["bar_1"]),
        instance,
        pipeline_run.run_id,
    )
    assert should_skip_step(
        create_execution_plan(optional_outputs, step_keys_to_execute=["bar_2"]),
        instance,
        pipeline_run.run_id,
    )
    assert should_skip_step(
        create_execution_plan(optional_outputs, step_keys_to_execute=["bar_3"]),
        instance,
        pipeline_run.run_id,
    )


def test_fan_in_should_skip_step():
    @lambda_solid
    def one():
        return 1

    @solid(output_defs=[OutputDefinition(is_required=False)])
    def skip(_):
        return
        yield  # pylint: disable=unreachable

    @solid
    def fan_in(_context, items):
        return items

    @composite_solid(output_defs=[OutputDefinition(is_required=False)])
    def composite_all_upstream_skip():
        return fan_in([skip(), skip()])

    @composite_solid(output_defs=[OutputDefinition(is_required=False)])
    def composite_one_upstream_skip():
        return fan_in([one(), skip()])

    @pipeline
    def optional_outputs_composite():
        composite_all_upstream_skip()
        composite_one_upstream_skip()

    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(pipeline_name="optional_outputs_composite", run_id=make_new_run_id())
    execute_plan(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=[
                "composite_all_upstream_skip.skip",
                "composite_all_upstream_skip.skip_2",
            ],
        ),
        instance,
        pipeline_run,
    )
    # skip when all the step's sources weren't yield
    assert should_skip_step(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=["composite_all_upstream_skip.fan_in"],
        ),
        instance,
        pipeline_run.run_id,
    )

    execute_plan(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=[
                "composite_one_upstream_skip.one",
                "composite_one_upstream_skip.skip",
            ],
        ),
        instance,
        pipeline_run,
    )
    # do not skip when some of the sources exist
    assert not should_skip_step(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=["composite_one_upstream_skip.fan_in"],
        ),
        instance,
        pipeline_run.run_id,
    )
