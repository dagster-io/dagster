import dagster as dg


# start_graph_backed_asset_foo
@dg.op(out={"foo_1": dg.Out(is_required=False), "foo_2": dg.Out(is_required=False)})
def foo(context: dg.OpExecutionContext, bar_1):
    # Selectively returns outputs based on selected assets
    if "foo_1" in context.selected_output_names:
        yield dg.Output(bar_1 + 1, output_name="foo_1")
    if "foo_2" in context.selected_output_names:
        yield dg.Output(bar_1 + 2, output_name="foo_2")


# end_graph_backed_asset_foo

# start_graph_backed_asset_example


@dg.op(out={"bar_1": dg.Out(), "bar_2": dg.Out()})
def bar():
    return 1, 2


@dg.op
def baz(foo_2, bar_2):
    return foo_2 + bar_2


@dg.graph_multi_asset(
    outs={"foo_asset": dg.AssetOut(), "baz_asset": dg.AssetOut()}, can_subset=True
)
def my_graph_assets():
    bar_1, bar_2 = bar()
    foo_1, foo_2 = foo(bar_1)
    return {"foo_asset": foo_1, "baz_asset": baz(foo_2, bar_2)}


defs = dg.Definitions(
    assets=[my_graph_assets], jobs=[dg.define_asset_job("graph_asset")]
)

# end_graph_backed_asset_example
