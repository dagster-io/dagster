import dagster as dg


@dg.op(out=dg.Out(int))
def return_one():
    return 1


@dg.op(out=dg.Out(int))
def return_two():
    return 2


@dg.op(ins={"int_1": dg.In(int)}, out=dg.Out(int))
def add_one(int_1):
    return int_1 + 1


@dg.op(ins={"int_1": dg.In(int), "int_2": dg.In(int)}, out=dg.Out(int))
def adder(int_1, int_2):
    return int_1 + int_2


@dg.op(out={"one": dg.Out(int), "two": dg.Out(int)})
def return_mult():
    return 1, 2


def test_single_ins():
    @dg.graph
    def composite_add_one(int_1):
        add_one(int_1)

    @dg.graph
    def my_graph():
        composite_add_one(return_one())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_add_one.add_one") == 2


def test_multi_ins():
    @dg.graph
    def composite_adder(int_1, int_2):
        adder(int_1, int_2)

    @dg.graph
    def my_graph():
        composite_adder(return_one(), return_two())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_adder.adder") == 3


def test_single_out():
    @dg.graph(out=dg.GraphOut())
    def composite_return_one():
        return return_one()

    @dg.graph
    def my_graph():
        composite_return_one()

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_return_one") == 1


def test_multi_out():
    called = {}

    @dg.graph(out={"out_1": dg.GraphOut(), "out_2": dg.GraphOut()})
    def composite_return_mult():
        one, two = return_mult()
        return (one, two)

    @dg.op
    def echo(in_one, in_two):
        called["one"] = in_one
        called["two"] = in_two

    @dg.graph
    def my_graph():
        one, two = composite_return_mult()  # pyright: ignore[reportGeneralTypeIssues]
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
    @dg.graph(out=dg.GraphOut())
    def inner_composite_add_one(int_1):
        return add_one(int_1)

    @dg.graph(out=dg.GraphOut())
    def composite_adder(int_1):
        return inner_composite_add_one(int_1)

    @dg.graph
    def my_graph():
        composite_adder(return_one())

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("composite_adder") == 2
    assert result.output_for_node("composite_adder.inner_composite_add_one") == 2
    assert result.output_for_node("composite_adder.inner_composite_add_one.add_one") == 2
