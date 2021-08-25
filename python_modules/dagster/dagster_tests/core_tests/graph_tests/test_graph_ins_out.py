from dagster.core.definitions.events import Output
from dagster.core.definitions.input import InSpec, In
from dagster.core.definitions.output import OutSpec, Out

import pytest
from dagster import graph, op
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.execute import execute_in_process


@op(out=Out(int))
def return_one():
    return 1


@op(out=Out(int))
def return_two():
    return 2


@op(ins={"int_1": In(int)}, out=Out(int))
def add_one(int_1):
    return int_1 + 1


@op(ins={"int_1": In(int), "int_2": In(int)}, out=Out(int))
def adder(int_1, int_2):
    return int_1 + int_2


@op(out={"one": Out(int), "two": Out(int)})
def return_mult():
    yield Output(1, "one")
    yield Output(2, "two")


def test_single_ins():
    @graph(ins={"int_1": InSpec(int)})
    def composite_add_one(int_1):
        add_one(int_1)

    @graph
    def pipe():
        composite_add_one(return_one())

    result = execute_in_process(pipe)
    assert result.success
    assert result.result_for_node("composite_add_one").result_for_node("add_one").output_values == {
        "result": 2
    }


def test_multi_ins():
    @graph(ins={"int_1": InSpec(int), "int_2": InSpec(int)})
    def composite_adder(int_1, int_2):
        adder(int_1, int_2)

    @graph
    def pipe():
        composite_adder(return_one(), return_two())

    result = execute_in_process(pipe)
    assert result.success
    assert result.result_for_node("composite_adder").result_for_node("adder").output_values == {
        "result": 3
    }


def test_ins_fail():
    with pytest.raises(DagsterInvalidDefinitionError):

        @graph(ins={"int_1": InSpec(), "int_2": InSpec()})
        def _fail(int_1, int_2):
            adder(int_1, int_2)


def test_single_out():
    @graph(out=OutSpec(int))
    def composite_return_one():
        return return_one()

    @graph
    def pipe():
        composite_return_one()

    result = execute_in_process(pipe)
    assert result.success
    assert result.result_for_node("composite_return_one").output_values == {"result": 1}


def test_multi_out():
    @graph(out={"out_1": OutSpec(int), "out_2": OutSpec(int)})
    def composite_return_mult():
        one, two = return_mult()
        return {"out_1": one, "out_2": two}

    @graph
    def pipe():
        composite_return_mult()

    result = execute_in_process(pipe)
    assert result.success
    assert result.result_for_node("composite_return_mult").output_values == {"out_1": 1, "out_2": 2}


def test_out_fail():

    with pytest.raises(DagsterInvalidDefinitionError):

        @graph(out=OutSpec(int))
        def _fail():
            return_one()


def test_graph_in_graph():
    @graph(ins={"int_1": InSpec(int)}, out=OutSpec(int))
    def inner_composite_add_one(int_1):
        return add_one(int_1)

    @graph(ins={"int_1": InSpec(int)}, out=OutSpec(int))
    def composite_adder(int_1):
        return inner_composite_add_one(int_1)

    @graph
    def pipe():
        composite_adder(return_one())

    result = execute_in_process(pipe)
    assert result.success
    assert result.result_for_node("composite_adder").output_values == {"result": 2}
    assert result.result_for_node("composite_adder").result_for_node(
        "inner_composite_add_one"
    ).output_values == {"result": 2}
    assert result.result_for_node("composite_adder").result_for_node(
        "inner_composite_add_one"
    ).result_for_node("add_one").output_values == {"result": 2}
