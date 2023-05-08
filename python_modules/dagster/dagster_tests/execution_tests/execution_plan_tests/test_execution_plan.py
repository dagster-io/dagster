import pytest
from dagster import (
    DagsterInstance,
    Int,
    Out,
    Output,
    _check as check,
    job,
    op,
)
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.output import GraphOut
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    DagsterUnknownStepStateError,
)
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.plan.plan import should_skip_step
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.utils import make_new_run_id


def define_diamond_job():
    @op
    def return_two():
        return 2

    @op
    def add_three(num):
        return num + 3

    @op
    def mult_three(num):
        return num * 3

    @op
    def adder(left, right):
        return left + right

    @job
    def diamond_job():
        two = return_two()
        adder(left=add_three(two), right=mult_three(two))

    return diamond_job


def test_topological_sort():
    plan = create_execution_plan(define_diamond_job())

    levels = plan.get_steps_to_execute_by_level()

    assert len(levels) == 3

    assert [step.key for step in levels[0]] == ["return_two"]
    assert [step.key for step in levels[1]] == ["add_three", "mult_three"]
    assert [step.key for step in levels[2]] == ["adder"]


def test_create_execution_plan_with_bad_inputs():
    with pytest.raises(DagsterInvalidConfigError):
        create_execution_plan(
            define_diamond_job(),
            run_config={"ops": {"add_three": {"inputs": {"num": 3}}}},
        )


def test_active_execution_plan():
    plan = create_execution_plan(define_diamond_job())

    with plan.start(retry_mode=(RetryMode.DISABLED)) as active_execution:
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
    job_def = define_diamond_job()
    plan = create_execution_plan(job_def)

    with plan.start(retry_mode=(RetryMode.DISABLED)) as active_execution:
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
    job_def = define_diamond_job()
    plan = create_execution_plan(job_def)

    with plan.start(retry_mode=(RetryMode.ENABLED)) as active_execution:
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
    job_def = define_diamond_job()
    plan = create_execution_plan(job_def)

    with pytest.raises(check.CheckError):
        with plan.start(retry_mode=(RetryMode.DISABLED)) as active_execution:
            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            assert step_1.key == "return_two"

            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 0  # cant progress

            # raises
            active_execution.mark_up_for_retry(step_1.key)


def test_retries_deferred_active_execution():
    job_def = define_diamond_job()
    plan = create_execution_plan(job_def)

    with plan.start(retry_mode=(RetryMode.DEFERRED)) as active_execution:
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
    @op(tags={"priority": 5})
    def pri_5(_):
        pass

    @op(tags={"priority": 4})
    def pri_4(_):
        pass

    @op(tags={"priority": 3})
    def pri_3(_):
        pass

    @op(tags={"priority": 2})
    def pri_2(_):
        pass

    @op(tags={"priority": -1})
    def pri_neg_1(_):
        pass

    @op
    def pri_none(_):
        pass

    @job
    def priorities():
        pri_neg_1()
        pri_3()
        pri_2()
        pri_none()
        pri_5()
        pri_4()

    sort_key_fn = lambda step: int(step.tags.get("priority", 0)) * -1

    plan = create_execution_plan(priorities)
    with plan.start(RetryMode.DISABLED, sort_key_fn) as active_execution:
        steps = active_execution.get_steps_to_execute()
        assert steps[0].key == "pri_5"
        assert steps[1].key == "pri_4"
        assert steps[2].key == "pri_3"
        assert steps[3].key == "pri_2"
        assert steps[4].key == "pri_none"
        assert steps[5].key == "pri_neg_1"
        _ = [active_execution.mark_skipped(step.key) for step in steps]


def test_tag_concurrency_limits():
    @op(tags={"database": "tiny", "dagster/priority": 5})
    def tiny_op_pri_5(_):
        pass

    @op(tags={"database": "large", "dagster/priority": 4})
    def large_op_pri_4(_):
        pass

    @op(tags={"dagster/priority": 3, "database": "tiny"})
    def tiny_op_pri_3(_):
        pass

    @op(tags={"dagster/priority": 2, "database": "large"})
    def large_op_pri_2(_):
        pass

    @op(tags={"dagster/priority": -1})
    def pri_neg_1(_):
        pass

    @op
    def pri_none(_):
        pass

    @job
    def tag_concurrency_limits_job():
        tiny_op_pri_5()
        large_op_pri_4()
        tiny_op_pri_3()
        large_op_pri_2()
        pri_neg_1()
        pri_none()

    plan = create_execution_plan(tag_concurrency_limits_job)

    tag_concurrency_limits = [
        {"key": "database", "value": "tiny", "limit": 1},
        {"key": "database", "value": "large", "limit": 2},
    ]

    with plan.start(
        RetryMode.DISABLED, tag_concurrency_limits=tag_concurrency_limits
    ) as active_execution:
        steps = active_execution.get_steps_to_execute()

        assert len(steps) == 5
        assert steps[0].key == "tiny_op_pri_5"
        assert steps[1].key == "large_op_pri_4"
        assert steps[2].key == "large_op_pri_2"
        assert steps[3].key == "pri_none"
        assert steps[4].key == "pri_neg_1"

        assert active_execution.get_steps_to_execute() == []

        active_execution.mark_skipped("tiny_op_pri_5")

        next_steps = active_execution.get_steps_to_execute()

        assert len(next_steps) == 1

        assert next_steps[0].key == "tiny_op_pri_3"

        for step_key in active_execution._in_flight.copy():  # noqa: SLF001
            active_execution.mark_skipped(step_key)


def test_executor_not_created_for_execute_plan():
    instance = DagsterInstance.ephemeral()
    pipe = define_diamond_job()
    plan = create_execution_plan(pipe)
    job_def = instance.create_run_for_job(pipe, plan)

    results = execute_plan(
        plan,
        InMemoryJob(pipe),
        instance,
        job_def,
    )
    for result in results:
        assert not result.is_failure


def test_incomplete_execution_plan():
    plan = create_execution_plan(define_diamond_job())

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Execution finished without completing the execution plan.",
    ):
        with plan.start(retry_mode=(RetryMode.DISABLED)) as active_execution:
            steps = active_execution.get_steps_to_execute()
            assert len(steps) == 1
            step_1 = steps[0]
            active_execution.mark_success(step_1.key)

            # exit early


def test_lost_steps():
    plan = create_execution_plan(define_diamond_job())

    # run to completion - but step was in unknown state so exception thrown
    with pytest.raises(DagsterUnknownStepStateError):
        with plan.start(retry_mode=(RetryMode.DISABLED)) as active_execution:
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
    @op(
        out={
            "out_1": Out(Int, is_required=False),
            "out_2": Out(Int, is_required=False),
            "out_3": Out(Int, is_required=False),
        }
    )
    def foo(_):
        yield Output(1, "out_1")

    @op
    def bar(_, input_arg):
        return input_arg

    @job
    def optional_outputs():
        foo_res = foo()

        bar.alias("bar_1")(input_arg=foo_res.out_1)
        bar.alias("bar_2")(input_arg=foo_res.out_2)
        bar.alias("bar_3")(input_arg=foo_res.out_3)

    instance = DagsterInstance.ephemeral()
    run = DagsterRun(job_name="optional_outputs", run_id=make_new_run_id())
    execute_plan(
        create_execution_plan(optional_outputs, step_keys_to_execute=["foo"]),
        InMemoryJob(optional_outputs),
        instance,
        run,
    )

    assert not should_skip_step(
        create_execution_plan(optional_outputs, step_keys_to_execute=["bar_1"]),
        instance,
        run.run_id,
    )
    assert should_skip_step(
        create_execution_plan(optional_outputs, step_keys_to_execute=["bar_2"]),
        instance,
        run.run_id,
    )
    assert should_skip_step(
        create_execution_plan(optional_outputs, step_keys_to_execute=["bar_3"]),
        instance,
        run.run_id,
    )


def test_fan_in_should_skip_step():
    @op
    def one():
        return 1

    @op(out=Out(is_required=False))
    def skip(_):
        return
        yield

    @op
    def fan_in(_context, items):
        return items

    @graph(out=GraphOut())
    def graph_all_upstream_skip():
        return fan_in([skip(), skip()])

    @graph(out=GraphOut())
    def graph_one_upstream_skip():
        return fan_in([one(), skip()])

    @job
    def optional_outputs_composite():
        graph_all_upstream_skip()
        graph_one_upstream_skip()

    instance = DagsterInstance.ephemeral()
    run = DagsterRun(job_name="optional_outputs_composite", run_id=make_new_run_id())
    execute_plan(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=[
                "graph_all_upstream_skip.skip",
                "graph_all_upstream_skip.skip_2",
            ],
        ),
        InMemoryJob(optional_outputs_composite),
        instance,
        run,
    )
    # skip when all the step's sources weren't yield
    assert should_skip_step(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=["graph_all_upstream_skip.fan_in"],
        ),
        instance,
        run.run_id,
    )

    execute_plan(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=[
                "graph_one_upstream_skip.one",
                "graph_one_upstream_skip.skip",
            ],
        ),
        InMemoryJob(optional_outputs_composite),
        instance,
        run,
    )
    # do not skip when some of the sources exist
    assert not should_skip_step(
        create_execution_plan(
            optional_outputs_composite,
            step_keys_to_execute=["graph_one_upstream_skip.fan_in"],
        ),
        instance,
        run.run_id,
    )


def test_configured_input_should_skip_step():
    called = {}

    @op(out=Out(is_required=False))
    def one(_):
        yield Output(1)

    @op
    def op_should_not_skip(_, input_one, input_two):
        called["yup"] = True

    @job
    def my_job():
        op_should_not_skip(one())

    run_config = {"ops": {"op_should_not_skip": {"inputs": {"input_two": {"value": "2"}}}}}
    my_job.execute_in_process(run_config=run_config)
    assert called.get("yup")

    # ensure should_skip_step behave the same as execute_job
    instance = DagsterInstance.ephemeral()
    run = DagsterRun(job_name="my_job", run_id=make_new_run_id())
    execute_plan(
        create_execution_plan(
            my_job,
            step_keys_to_execute=["one"],
            run_config=run_config,
        ),
        InMemoryJob(my_job),
        instance,
        run,
        run_config=run_config,
    )
    assert not should_skip_step(
        create_execution_plan(
            my_job,
            step_keys_to_execute=["op_should_not_skip"],
            run_config=run_config,
        ),
        instance,
        run.run_id,
    )
