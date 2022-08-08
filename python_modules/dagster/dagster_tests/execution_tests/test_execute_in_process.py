import pytest

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DagsterInvariantViolationError,
    DynamicOut,
    DynamicOutput,
    Out,
    Output,
    daily_partitioned_config,
    job,
    op,
    resource,
)
from dagster._check import CheckError
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.output import GraphOut
from dagster._legacy import solid


def get_solids():
    @op
    def emit_one():
        return 1

    @op
    def add(x, y):
        return x + y

    return emit_one, add


def test_output_value():
    @graph
    def a():
        get_solids()[0]()

    result = a.execute_in_process()

    assert result.success
    assert result.output_for_node("emit_one") == 1


def test_output_values():
    @op(out={"a": Out(), "b": Out()})
    def two_outs():
        return 1, 2

    @graph
    def a():
        two_outs()

    result = a.execute_in_process()

    assert result.success
    assert result.output_for_node("two_outs", "a") == 1
    assert result.output_for_node("two_outs", "b") == 2


def test_dynamic_output_values():
    @op(out=DynamicOut())
    def two_outs():
        yield DynamicOutput(1, "a")
        yield DynamicOutput(2, "b")

    @op
    def add_one(x):
        return x + 1

    @graph
    def a():
        two_outs().map(add_one)

    result = a.execute_in_process()

    assert result.success
    assert result.output_for_node("two_outs") == {"a": 1, "b": 2}
    assert result.output_for_node("add_one") == {"a": 2, "b": 3}


def test_execute_graph():
    emit_one, add = get_solids()

    @graph
    def emit_two():
        return add(emit_one(), emit_one())

    @graph
    def emit_three():
        return add(emit_two(), emit_one())

    result = emit_three.execute_in_process()

    assert result.success

    assert result.output_value() == 3

    assert result.output_for_node("add") == 3
    assert result.output_for_node("emit_two") == 2
    assert result.output_for_node("emit_one") == 1
    assert result.output_for_node("emit_two.emit_one") == 1
    assert result.output_for_node("emit_two.emit_one_2") == 1


def test_graph_with_required_resources():
    @op(required_resource_keys={"a"})
    def basic_reqs(context):
        return context.resources.a

    @graph
    def basic_graph():
        return basic_reqs()

    result = basic_graph.execute_in_process(resources={"a": "foo"})
    assert result.output_value() == "foo"

    @resource
    def basic_resource():
        return "bar"

    result = basic_graph.execute_in_process(resources={"a": basic_resource})
    assert result.output_value() == "bar"


def test_executor_config_ignored_by_execute_in_process():
    # Ensure that execute_in_process is able to properly ignore provided executor config.
    @op
    def my_op():
        return 0

    @graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job(
        config={"execution": {"config": {"multiprocess": {"max_concurrent": 5}}}}
    )

    result = my_job.execute_in_process()
    assert result.success


def test_output_for_node_composite():
    @op(out={"foo": Out()})
    def my_op():
        return 5

    @graph(out={"bar": GraphOut()})
    def my_graph():
        return my_op()

    @graph(out={"baz": GraphOut()})
    def my_top_graph():
        return my_graph()

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op", "foo") == 5
    assert result.output_value("bar") == 5

    result = my_top_graph.execute_in_process()
    assert result.output_for_node("my_graph", "bar") == 5
    assert result.output_for_node("my_graph.my_op", "foo") == 5
    assert result.output_value("baz") == 5


def test_output_for_node_not_found():
    @op
    def op_exists():
        return 5

    @graph
    def basic():
        return op_exists()

    result = basic.execute_in_process()
    assert result.success

    with pytest.raises(KeyError, match="name_doesnt_exist"):
        result.output_for_node("op_exists", "name_doesnt_exist")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Could not find top-level output 'name_doesnt_exist'",
    ):
        result.output_value("name_doesnt_exist")

    with pytest.raises(CheckError, match="basic has no op named op_doesnt_exist"):
        result.output_for_node("op_doesnt_exist")


def _get_step_successes(event_list):
    return [event for event in event_list if event.is_step_success]


def test_step_events_for_node():
    @op
    def op_exists():
        return 5

    @graph
    def basic():
        return op_exists()

    @graph
    def nested():
        return basic()

    result = nested.execute_in_process()
    node_events = result.all_node_events
    assert len(_get_step_successes(node_events)) == 1

    basic_events = result.events_for_node("basic")
    assert len(_get_step_successes(basic_events)) == 1

    op_events = result.events_for_node("basic.op_exists")
    assert len(_get_step_successes(op_events)) == 1


def test_output_value_error():
    @job
    def my_job():
        pass

    result = my_job.execute_in_process()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to retrieve top-level outputs for 'my_job', which has no outputs.",
    ):
        result.output_value()


def test_partitions_key():
    @op
    def my_op(context):
        assert (
            context._step_execution_context.plan_data.pipeline_run.tags[  # pylint: disable=protected-access
                "dagster/partition"
            ]
            == "2020-01-01"
        )

    @daily_partitioned_config(start_date="2020-01-01")
    def my_partitioned_config(_start, _end):
        return {}

    @job(config=my_partitioned_config)
    def my_job():
        my_op()

    assert my_job.execute_in_process(partition_key="2020-01-01").success


def test_asset_materialization():
    @op(out={})
    def my_op():
        yield AssetMaterialization("abc")

    @job
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    assert result.asset_materializations_for_node("my_op") == [
        AssetMaterialization(asset_key=AssetKey(["abc"]))
    ]


def test_asset_observation():
    @op(out={})
    def my_op():
        yield AssetObservation("abc")

    @job
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    assert result.asset_observations_for_node("my_op") == [
        AssetObservation(asset_key=AssetKey(["abc"]))
    ]


def test_dagster_run():
    @op
    def success_op():
        return True

    @job
    def my_success_job():
        success_op()

    result = my_success_job.execute_in_process()
    assert result.success
    assert result.dagster_run.is_success

    @op
    def fail_op():
        raise Exception

    @job
    def my_failure_job():
        fail_op()

    result = my_failure_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert not result.dagster_run.is_success


def test_dynamic_output_for_node():
    @op(out=DynamicOut())
    def fanout():
        for i in range(3):
            yield DynamicOutput(value=i, mapping_key=str(i))

    @op(
        out={
            "output1": Out(int),
            "output2": Out(int),
        }
    )
    def return_as_tuple(x):
        yield Output(value=x, output_name="output1")
        yield Output(value=5, output_name="output2")

    @job
    def myjob():
        fanout().map(return_as_tuple)

    # get result
    result = myjob.execute_in_process()

    # assertions
    assert result.output_for_node("return_as_tuple", "output1") == {
        "0": 0,
        "1": 1,
        "2": 2,
    }
    assert result.output_for_node("return_as_tuple", "output2") == {
        "0": 5,
        "1": 5,
        "2": 5,
    }


def test_execute_in_process_input_values():
    @op
    def requires_input_op(x: int):
        return x + 1

    @graph
    def requires_input_graph(x):
        return requires_input_op(x)

    result = requires_input_graph.alias("named_graph").execute_in_process(
        input_values={"x": 5}
    )
    assert result.success
    assert result.output_value() == 6
    result = requires_input_graph.to_job().execute_in_process(input_values={"x": 5})
    assert result.success
    assert result.output_value() == 6
