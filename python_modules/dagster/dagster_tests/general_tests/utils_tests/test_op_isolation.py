import re

import pytest
from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    Field,
    Int,
    op,
    resource,
)
from dagster._core.definitions.decorators import graph
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster._core.test_utils import nesting_graph
from dagster._core.utility_ops import (
    create_op_with_deps,
    create_root_op,
    create_stub_op,
    input_set,
)
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_single_op_in_isolation():
    @op
    def op_one():
        return 1

    result = wrap_op_in_graph_and_execute(op_one)
    assert result.success
    assert result.output_value() == 1


def test_single_op_with_single():
    @op(ins={"num": In()})
    def add_one_op(num):
        return num + 1

    result = wrap_op_in_graph_and_execute(add_one_op, input_values={"num": 2})

    assert result.success
    assert result.output_value() == 3


def test_single_op_with_multiple_inputs():
    @op(ins={"num_one": In(), "num_two": In()})
    def add_op(num_one, num_two):
        return num_one + num_two

    result = wrap_op_in_graph_and_execute(
        add_op,
        input_values={"num_one": 2, "num_two": 3},
        run_config={"loggers": {"console": {"config": {"log_level": "DEBUG"}}}},
    )

    assert result.success
    assert result.output_value() == 5


def test_single_op_with_config():
    ran = {}

    @op(config_schema=Int)
    def check_config_for_two(context):
        assert context.op_config == 2
        ran["check_config_for_two"] = True

    result = wrap_op_in_graph_and_execute(
        check_config_for_two,
        run_config={"ops": {"check_config_for_two": {"config": 2}}},
    )

    assert result.success
    assert ran["check_config_for_two"]


def test_single_op_with_context_config():
    @resource(config_schema=Field(Int, is_required=False, default_value=2))
    def num_resource(init_context):
        return init_context.resource_config

    ran = {"count": 0}

    @op(required_resource_keys={"num"})
    def check_context_config_for_two(context):
        assert context.resources.num == 2
        ran["count"] += 1

    result = wrap_op_in_graph_and_execute(
        check_context_config_for_two,
        run_config={"resources": {"num": {"config": 2}}},
        resources={"num": num_resource},
    )

    assert result.success
    assert ran["count"] == 1

    result = wrap_op_in_graph_and_execute(
        check_context_config_for_two,
        resources={"num": num_resource},
    )

    assert result.success
    assert ran["count"] == 2


def test_single_op_error():
    class SomeError(Exception):
        pass

    @op
    def throw_error():
        raise SomeError()

    with pytest.raises(SomeError) as e_info:
        wrap_op_in_graph_and_execute(throw_error)

    assert isinstance(e_info.value, SomeError)


def test_single_op_type_checking_output_error():
    @op(out=Out(Int))
    def return_string():
        return "ksjdfkjd"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(return_string)


def test_failing_op_in_isolation():
    class ThisException(Exception):
        pass

    @op
    def throw_an_error():
        raise ThisException("nope")

    with pytest.raises(ThisException) as e_info:
        wrap_op_in_graph_and_execute(throw_an_error)

    assert isinstance(e_info.value, ThisException)


def test_graphs():
    @op
    def hello():
        return "hello"

    @graph
    def hello_graph():
        return hello()

    result = wrap_op_in_graph_and_execute(hello)
    assert result.success
    assert result.output_value() == "hello"

    result = hello_graph.execute_in_process()
    assert result.success
    assert result.output_value() == "hello"
    assert result.output_for_node("hello") == "hello"

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("hello_graph has no op named goodbye"),
    ):
        _ = result.output_for_node("goodbye")


def test_graph_with_no_output_mappings():
    a_source = create_stub_op("A_source", [input_set("A_input")])
    node_a = create_root_op("A")
    node_b = create_op_with_deps("B", node_a)
    node_c = create_op_with_deps("C", node_a)
    node_d = create_op_with_deps("D", node_b, node_c)

    @graph
    def diamond_graph():
        a = node_a(a_source())
        node_d(B=node_b(a), C=node_c(a))

    res = diamond_graph.execute_in_process()

    assert res.success

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "Attempted to retrieve top-level outputs for 'diamond_graph', which has no outputs."
        ),
    ):
        _ = res.output_value()

    assert res.output_for_node("A_source")
    assert res.output_for_node("A")
    assert res.output_for_node("B")
    assert res.output_for_node("C")
    assert res.output_for_node("D")


def test_execute_nested_graphs():
    nested_graph_job = nesting_graph(2, 2).to_job()
    nested_graph = nested_graph_job.nodes[0].definition

    res = nested_graph.execute_in_process()

    assert res.success

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("Attempted to retrieve top-level outputs for 'layer_0'"),
    ):
        _ = res.output_value()

    assert res.output_for_node("layer_0_node_0.layer_1_node_0.layer_2_node_0") == 1
    assert res.output_for_node("layer_0_node_0.layer_1_node_0.layer_2_node_1") == 1
    assert res.output_for_node("layer_0_node_0.layer_1_node_1.layer_2_node_0") == 1
    assert res.output_for_node("layer_0_node_0.layer_1_node_1.layer_2_node_1") == 1
    assert res.output_for_node("layer_0_node_1.layer_1_node_0.layer_2_node_0") == 1
    assert res.output_for_node("layer_0_node_1.layer_1_node_0.layer_2_node_1") == 1
    assert res.output_for_node("layer_0_node_1.layer_1_node_1.layer_2_node_0") == 1
    assert res.output_for_node("layer_0_node_1.layer_1_node_1.layer_2_node_1") == 1


def test_single_op_with_bad_inputs():
    @op(ins={"num_one": In(int), "num_two": In(int)})
    def add_op(num_one, num_two):
        return num_one + num_two

    result = wrap_op_in_graph_and_execute(
        add_op,
        input_values={"num_one": 2, "num_two": "three"},
        run_config={"loggers": {"console": {"config": {"log_level": "DEBUG"}}}},
        raise_on_error=False,
    )

    assert not result.success
    failure_data = result.failure_data_for_node("add_op")
    assert failure_data.error.cls_name == "DagsterTypeCheckDidNotPass"
    assert (
        'Type check failed for step input "num_two" - expected type "Int"'
        in failure_data.error.message
    )
