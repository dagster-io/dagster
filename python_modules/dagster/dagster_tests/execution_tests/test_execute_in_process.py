import pytest
from dagster import (
    DagsterInvariantViolationError,
    DynamicOut,
    DynamicOutput,
    Out,
    op,
    resource,
    solid,
)
from dagster.core.definitions.decorators.graph import graph


def get_solids():
    @solid
    def emit_one():
        return 1

    @solid
    def add(x, y):
        return x + y

    return emit_one, add


def test_output_value():
    @graph
    def a():
        get_solids()[0]()

    result = a.execute_in_process()

    assert result.success
    assert result.result_for_node("emit_one").output_value() == 1


def test_output_values():
    @op(out={"a": Out(), "b": Out()})
    def two_outs():
        return 1, 2

    @graph
    def a():
        two_outs()

    result = a.execute_in_process()

    assert result.success
    assert result.result_for_node("two_outs").output_values["a"] == 1
    assert result.result_for_node("two_outs").output_values["b"] == 2


def test_dynamic_output_values():
    @op(out=DynamicOut())
    def two_outs():
        yield DynamicOutput(1, "a")
        yield DynamicOutput(2, "b")

    @graph
    def a():
        two_outs()

    result = a.execute_in_process()

    assert result.success
    assert result.result_for_node("two_outs").output_value() == {"a": 1, "b": 2}


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

    assert result.output_values["result"] == 3
    assert result.result_for_node("add").output_values["result"] == 3
    assert result.result_for_node("emit_two").output_values["result"] == 2
    assert result.result_for_node("emit_one").output_values["result"] == 1
    assert (
        result.result_for_node("emit_two").result_for_node("emit_one").output_values["result"] == 1
    )
    assert (
        result.result_for_node("emit_two").result_for_node("emit_one_2").output_values["result"]
        == 1
    )


def test_graph_with_required_resources():
    @solid(required_resource_keys={"a"})
    def basic_reqs(context):
        return context.resources.a

    @graph
    def basic_graph():
        return basic_reqs()

    result = basic_graph.execute_in_process(resources={"a": "foo"})
    assert result.output_values["result"] == "foo"

    @resource
    def basic_resource():
        return "bar"

    result = basic_graph.execute_in_process(resources={"a": basic_resource})
    assert result.output_values["result"] == "bar"


def test_executor_config_ignored_by_execute_in_process():
    # Ensure that execute_in_process is able to properly ignore provided executor config.
    @solid
    def my_solid():
        return 0

    @graph
    def my_graph():
        my_solid()

    my_job = my_graph.to_job(
        config={"execution": {"multiprocess": {"config": {"max_concurrent": 5}}}}
    )

    result = my_job.execute_in_process()
    assert result.success


def test_graph_with_inputs_error():
    @solid
    def my_solid(x):
        return x

    @graph
    def my_graph(x):
        my_solid(x)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Graphs with inputs cannot be used with execute_in_process at this time.",
    ):
        my_graph.execute_in_process()
