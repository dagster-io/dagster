import pytest

from dagster import (
    DynamicOut,
    DynamicOutput,
    Field,
    Out,
    Output,
    ReexecutionOptions,
    execute_job,
    graph,
    job,
    op,
    reconstructable,
)
from dagster._core.errors import DagsterExecutionStepNotFoundError
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.test_utils import instance_for_test
from dagster._utils import merge_dicts


@op(tags={"third": "3"})
def multiply_by_two(context, y):
    context.log.info("multiply_by_two is returning " + str(y * 2))
    return y * 2


@op(tags={"second": "2"})
def multiply_inputs(context, y, ten):
    context.log.info("multiply_inputs is returning " + str(y * ten))
    return y * ten


@op
def emit_ten(_):
    return 10


@op
def echo(_, x: int) -> int:
    return x


@op(
    config_schema={
        "range": Field(int, is_required=False, default_value=3),
    }
)
def num_range(context) -> int:
    return context.op_config["range"]


@op(
    out=DynamicOut(),
    config_schema={
        "fail": Field(bool, is_required=False, default_value=False),
    },
    tags={"first": "1"},
)
def emit(context, num: int = 3):
    if context.op_config["fail"]:
        raise Exception("FAILURE")

    for i in range(num):
        yield DynamicOutput(value=i, mapping_key=str(i))


@op
def sum_numbers(_, nums):
    return sum(nums)


@op(out=DynamicOut())
def dynamic_echo(_, nums):
    for x in nums:
        yield DynamicOutput(value=x, mapping_key=str(x))


@job
def dynamic_pipeline():

    numbers = emit(num_range())
    dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
    n = multiply_by_two.alias("double_total")(sum_numbers(dynamic.collect()))
    echo(n)  # test transitive downstream of collect


@job
def fan_repeat():
    one = emit(num_range()).map(multiply_by_two)
    two = dynamic_echo(one.collect()).map(multiply_by_two).map(echo)
    three = dynamic_echo(two.collect()).map(multiply_by_two)
    sum_numbers(three.collect())


def _step_keys_from_result(result):
    return set([event.step_key for event in result.all_events if event.step_key is not None])


def _in_proc_cfg():
    return {
        "execution": {
            "config": {
                "in_process": {},
            }
        }
    }


def _mp_cfg():
    return {
        "execution": {
            "config": {
                "multiprocess": {
                    "start_method": {"forkserver": {}},
                }
            }
        }
    }


def _run_configs():
    return [
        _in_proc_cfg(),
        _mp_cfg(),
    ]


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_map(run_config):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=run_config,
        ) as result:
            assert result.success
            keys = _step_keys_from_result(result)
            assert "multiply_inputs[0]" in keys
            assert "multiply_inputs[1]" in keys
            assert "multiply_inputs[2]" in keys
            assert result.output_for_node("multiply_inputs") == {
                "0": 0,
                "1": 10,
                "2": 20,
            }
            assert result.output_for_node("multiply_by_two") == {
                "0": 0,
                "1": 20,
                "2": 40,
            }
            assert result.output_for_node("sum_numbers") == 60
            assert result.output_for_node("double_total") == 120
            assert result.output_for_node("echo") == 120


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_map_empty(run_config):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=merge_dicts({"ops": {"num_range": {"config": {"range": 0}}}}, run_config),
        ) as result:
            assert result.success
            assert result.output_for_node("double_total") == 0


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_map_selection(run_config):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=merge_dicts({"ops": {"emit": {"inputs": {"num": 2}}}}, run_config),
            op_selection=["emit*", "emit_ten"],
        ) as result:
            assert result.success
            assert result.output_for_node("double_total") == 40


def test_composite_wrapping():
    # regression test from user report

    @graph
    def do_multiple_steps(z):
        output = echo(z)
        return echo(output)

    @job
    def shallow():
        emit().map(do_multiple_steps)

    result = shallow.execute_in_process()
    assert result.success
    assert result.output_for_node("do_multiple_steps") == {
        "0": 0,
        "1": 1,
        "2": 2,
    }

    @graph
    def inner(x):
        return echo(x)

    @graph
    def middle(y):
        return inner(y)

    @graph
    def outer(z):
        return middle(z)

    @job
    def deep():
        emit().map(outer)

    result = deep.execute_in_process()
    assert result.success
    assert result.output_for_node("outer") == {"0": 0, "1": 1, "2": 2}


def test_tags():
    known_state = KnownExecutionState(
        {},
        {
            emit.name: {"result": ["0", "1", "2"]},
        },
    )
    plan = create_execution_plan(dynamic_pipeline, known_state=known_state)

    assert plan.get_step_by_key(emit.name).tags == {"first": "1"}

    for mapping_key in range(3):
        assert plan.get_step_by_key(f"{multiply_inputs.name}[{mapping_key}]").tags == {
            "second": "2"
        }
        assert plan.get_step_by_key(f"{multiply_by_two.name}[{mapping_key}]").tags == {"third": "3"}


def test_full_reexecute():
    with instance_for_test() as instance:
        result_1 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=_in_proc_cfg(),
        )
        assert result_1.success

        result_2 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=_in_proc_cfg(),
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
            ),
        )
        assert result_2.success


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_partial_reexecute(run_config):
    with instance_for_test() as instance:
        result_1 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=run_config,
        )
        assert result_1.success

        result_2 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=run_config,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["sum_numbers*"],
            ),
        )
        assert result_2.success

        result_3 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=run_config,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["multiply_by_two[1]*"],
            ),
        )
        assert result_3.success


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_fan_out_in_out_in(run_config):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(fan_repeat),
            instance=instance,
            run_config=run_config,
        ) as result:
            assert result.success
            assert result.output_for_node("sum_numbers") == 24  # (0, 1, 2) x 2 x 2 x 2 = (0, 8, 16)

        with execute_job(
            reconstructable(fan_repeat),
            instance=instance,
            run_config={"ops": {"num_range": {"config": {"range": 0}}}},
        ) as empty_result:
            assert empty_result.success
            assert empty_result.output_for_node("sum_numbers") == 0


def test_select_dynamic_step_and_downstream():
    with instance_for_test() as instance:
        result_1 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=_in_proc_cfg(),
        )
        assert result_1.success

        result_2 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=_in_proc_cfg(),
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["+multiply_inputs[?]"],
            ),
        )
        assert result_2.success

        with execute_job(
            reconstructable(dynamic_pipeline),
            run_config=_in_proc_cfg(),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["emit*"],
            ),
        ) as result_3:
            assert result_3.success

            keys_3 = _step_keys_from_result(result_3)
            assert "multiply_inputs[0]" in keys_3
            assert "multiply_inputs[1]" in keys_3
            assert "multiply_inputs[2]" in keys_3
            assert "multiply_by_two[0]" in keys_3
            assert "multiply_by_two[1]" in keys_3
            assert "multiply_by_two[2]" in keys_3
            assert result_3.output_for_node("double_total") == 120

        result_4 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["emit+"],
            ),
        )
        assert result_4.success

        keys_4 = _step_keys_from_result(result_4)
        assert "multiply_inputs[0]" in keys_4
        assert "multiply_inputs[1]" in keys_4
        assert "multiply_inputs[2]" in keys_4
        assert "multiply_by_two[0]" not in keys_4

        result_5 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
                step_selection=["emit", "multiply_inputs[?]"],
            ),
        )
        assert result_5.success

        keys_5 = _step_keys_from_result(result_5)
        assert "multiply_inputs[0]" in keys_5
        assert "multiply_inputs[1]" in keys_5
        assert "multiply_inputs[2]" in keys_5
        assert "multiply_by_two[0]" not in keys_5


def test_bad_step_selection():
    with instance_for_test() as instance:
        result_1 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=_in_proc_cfg(),
        )
        assert result_1.success

        # this exact error could be improved, but it should fail if you try to select
        # both the dynamic outputting step key and something resolved by it in the previous run
        with pytest.raises(DagsterExecutionStepNotFoundError):
            execute_job(
                reconstructable(dynamic_pipeline),
                instance=instance,
                reexecution_options=ReexecutionOptions(
                    parent_run_id=result_1.run_id,
                    step_selection=["emit", "multiply_by_two[1]"],
                ),
            )


def define_real_dynamic_job():
    @op(config_schema=list, out=DynamicOut(int))
    def generate_subtasks(context):
        for num in context.op_config:
            yield DynamicOutput(num, mapping_key=str(num))

    @op
    def subtask(input_number: int):
        return input_number

    @job
    def real_dynamic_job():
        generate_subtasks().map(subtask)

    return real_dynamic_job


def test_select_dynamic_step_with_non_static_mapping():
    with instance_for_test() as instance:
        result_0 = execute_job(
            reconstructable(define_real_dynamic_job),
            instance=instance,
            run_config={"ops": {"generate_subtasks": {"config": [0, 2, 4]}}},
        )
        assert result_0.success

        # Should generate dynamic steps using the outs in current run
        result_1 = execute_job(
            reconstructable(define_real_dynamic_job),
            instance=instance,
            run_config={"ops": {"generate_subtasks": {"config": [0, 1, 2, 3, 4]}}},
            reexecution_options=ReexecutionOptions(
                step_selection=["generate_subtasks+"],
                parent_run_id=result_0.run_id,
            ),
        )
        assert result_1.success
        keys_1 = _step_keys_from_result(result_1)
        assert "generate_subtasks" in keys_1
        assert "subtask[0]" in keys_1
        assert "subtask[1]" in keys_1
        assert "subtask[2]" in keys_1
        assert "subtask[3]" in keys_1
        assert "subtask[4]" in keys_1

        # Should generate dynamic steps using the outs in current run
        result_2 = execute_job(
            reconstructable(define_real_dynamic_job),
            instance=instance,
            run_config={"ops": {"generate_subtasks": {"config": [1, 2, 3]}}},
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_0.run_id,
                step_selection=["+subtask[?]"],
            ),
        )
        assert result_2.success
        keys_2 = _step_keys_from_result(result_2)
        assert "generate_subtasks" in keys_2
        assert "subtask[0]" not in keys_2
        assert "subtask[1]" in keys_2
        assert "subtask[2]" in keys_2
        assert "subtask[3]" in keys_2
        assert "subtask[4]" not in keys_2


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_map_fail(run_config):
    with instance_for_test() as instance:
        result = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=merge_dicts({"ops": {"emit": {"config": {"fail": True}}}}, run_config),
            raise_on_error=False,
        )
        assert not result.success


@pytest.mark.parametrize(
    "run_config",
    _run_configs(),
)
def test_map_reexecute_after_fail(run_config):
    with instance_for_test() as instance:
        result_1 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=merge_dicts(
                run_config,
                {"ops": {"emit": {"config": {"fail": True}}}},
            ),
            raise_on_error=False,
        )
        assert not result_1.success

        result_2 = execute_job(
            reconstructable(dynamic_pipeline),
            instance=instance,
            run_config=run_config,
            reexecution_options=ReexecutionOptions(
                parent_run_id=result_1.run_id,
            ),
        )
        assert result_2.success


def test_multi_collect():
    @op
    def fan_in(_, x, y):
        return x + y

    @job
    def double():
        nums_1 = emit()
        nums_2 = emit()
        fan_in(nums_1.collect(), nums_2.collect())

    result = double.execute_in_process()
    assert result.success
    assert result.output_for_node("fan_in") == [0, 1, 2, 0, 1, 2]


def test_fan_in_skips():
    @op(
        out={
            "nums": Out(),
            "empty": Out(),
            "skip": Out(is_required=False),
        }
    )
    def fork_logic():
        yield Output([1, 2, 3], output_name="nums")
        yield Output([], output_name="empty")

    @op(out=DynamicOut(int))
    def emit_dyn(vector):
        for i in vector:
            yield DynamicOutput(value=i, mapping_key=f"input_{i}")

    @op
    def total(items):
        return sum(items)

    @job
    def dyn_fork():
        nums, empty, skip = fork_logic()
        total.alias("grand_total")(
            [
                total.alias("nums_total")(emit_dyn(nums).map(echo).collect()),
                total.alias("empty_total")(emit_dyn(empty).map(echo).collect()),
                total.alias("skip_total")(emit_dyn(skip).map(echo).collect()),
            ]
        )

    result = dyn_fork.execute_in_process()
    assert result.success

    assert result.output_for_node("nums_total")
    assert result.output_for_node("empty_total") == 0

    assert result.output_for_node("skip_total") == 0  # arguably should skip

    assert result.output_for_node("grand_total") == 6
