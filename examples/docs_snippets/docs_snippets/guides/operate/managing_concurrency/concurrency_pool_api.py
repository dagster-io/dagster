import dagster as dg


@dg.asset(pool="foo")
def my_asset():
    pass


@dg.op(pool="bar")
def my_op():
    pass


@dg.op(pool="barbar")
def my_downstream_op(inp):
    return inp


@dg.graph_asset
def my_graph_asset():
    return my_downstream_op(my_op())
