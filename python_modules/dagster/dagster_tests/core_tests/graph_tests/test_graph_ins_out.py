from dagster import graph, op
from dagster.core.definitions.input import In
from dagster.core.definitions.output import GraphOut, Out


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
    @graph
    def composite_add_one(int_1):
        add_one(int_1)

    @graph
    def my_graph():
        composite_add_one(return_one())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_add_one.add_one") == 2


def test_multi_ins():
    @graph
    def composite_adder(int_1, int_2):
        adder(int_1, int_2)

    @graph
    def my_graph():
        composite_adder(return_one(), return_two())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_adder.adder") == 3


def test_single_out():
    @graph(out=GraphOut())
    def composite_return_one():
        return return_one()

    @graph
    def my_graph():
        composite_return_one()

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_return_one") == 1


def test_multi_out():
    called = {}

    @graph(out={"out_1": GraphOut(), "out_2": GraphOut()})
    def composite_return_mult():
        one, two = return_mult()
        return (one, two)

    @op
    def echo(in_one, in_two):
        called["one"] = in_one
        called["two"] = in_two

    @graph
    def my_graph():
        one, two = composite_return_mult()
        echo(one, two)

    result = composite_return_mult.execute_in_process()
    assert result.output_value("out_1") == 1
    assert result.output_value("out_2") == 2

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_return_mult", "out_1") == 1
    assert result.output_for_node("composite_return_mult", "out_2") == 2
    assert called == {"one": 1, "two": 2}


def test_graph_in_graph():
    @graph(out=GraphOut())
    def inner_composite_add_one(int_1):
        return add_one(int_1)

    @graph(out=GraphOut())
    def composite_adder(int_1):
        return inner_composite_add_one(int_1)

    @graph
    def my_graph():
        composite_adder(return_one())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_adder") == 2
    assert result.output_for_node("composite_adder.inner_composite_add_one") == 2
    assert result.output_for_node("composite_adder.inner_composite_add_one.add_one") == 2
