import pytest
from dagster import graph, op
from dagster.core.definitions.input import GraphIn, In
from dagster.core.definitions.output import GraphOut, Out
from dagster.core.errors import DagsterInvalidDefinitionError


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
    return 1, 2


def test_single_ins():
    @graph(ins={"int_1": GraphIn()})
    def composite_add_one(int_1):
        add_one(int_1)

    @graph
    def my_graph():
        composite_add_one(return_one())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.result_for_node("composite_add_one").result_for_node("add_one").output_values == {
        "result": 2
    }


def test_multi_ins():
    @graph(ins={"int_1": GraphIn(), "int_2": GraphIn()})
    def composite_adder(int_1, int_2):
        adder(int_1, int_2)

    @graph
    def my_graph():
        composite_adder(return_one(), return_two())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.result_for_node("composite_adder").result_for_node("adder").output_values == {
        "result": 3
    }


# def test_ins_fail():
#     with pytest.raises(DagsterInvalidDefinitionError):

#         @graph(ins={"int_1": GraphIn(), "int_2": GraphIn()})
#         def _fail(int_1, int_2):
#             adder(int_1, int_2)

#     with pytest.raises(DagsterInvalidDefinitionError):

#         @graph(ins={"int_1": GraphIn(str), "int_2": GraphIn(str)})
#         def _fail(int_1, int_2):
#             adder(int_1, int_2)

#     with pytest.raises(DagsterInvalidDefinitionError):

#         @graph(ins={"int_1": GraphIn(int)}, out=GraphOut())
#         def inner_composite_add_one(int_1):
#             return add_one(int_1)

#         @graph(ins={"int_1": GraphIn(str)})
#         def _fail(int_1):
#             inner_composite_add_one(int_1)


def test_single_out():
    @graph(out=GraphOut())
    def composite_return_one():
        return return_one()

    @graph
    def my_graph():
        composite_return_one()

    result = my_graph.execute_in_process()
    assert result.success
    assert result.result_for_node("composite_return_one").output_values == {"result": 1}


def test_multi_out():
    @graph(out={"out_1": GraphOut(), "out_2": GraphOut()})
    def composite_return_mult():
        one, two = return_mult()
        return {"out_1": one, "out_2": two}

    @graph
    def my_graph():
        composite_return_mult()

    result = my_graph.execute_in_process()
    assert result.success
    assert result.result_for_node("composite_return_mult").output_values == {"out_1": 1, "out_2": 2}


# def test_out_fail():

#     # with pytest.raises(DagsterInvalidDefinitionError):

#     #     @graph(out=GraphOut())
#     #     def _fail():
#     #         return_one()

#     # with pytest.raises(DagsterInvalidDefinitionError):

#     #     @graph(out=GraphOut())
#     #     def _fail():
#     #         return return_one()

#     with pytest.raises(DagsterInvalidDefinitionError):

#         @graph(ins={"int_1": GraphIn()}, out=GraphOut())
#         def inner_composite_add_one(int_1):
#             return add_one(int_1)

#         @graph(ins={"int_1": GraphIn()}, out=GraphOut())
#         def _fail(int_1):
#             return inner_composite_add_one(int_1)


def test_graph_in_graph():
    @graph(ins={"int_1": GraphIn()}, out=GraphOut())
    def inner_composite_add_one(int_1):
        return add_one(int_1)

    @graph(ins={"int_1": GraphIn()}, out=GraphOut())
    def composite_adder(int_1):
        return inner_composite_add_one(int_1)

    @graph
    def my_graph():
        composite_adder(return_one())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.result_for_node("composite_adder").output_values == {"result": 2}
    assert result.result_for_node("composite_adder").result_for_node(
        "inner_composite_add_one"
    ).output_values == {"result": 2}
    assert result.result_for_node("composite_adder").result_for_node(
        "inner_composite_add_one"
    ).result_for_node("add_one").output_values == {"result": 2}
