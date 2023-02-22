from dagster import AssetKey, Out, op

from .subset_graph_backed_asset import defs


# start_unexpected_materialization_foo
@op(out={"foo_1": Out(), "foo_2": Out()})
def foo():
    return 1, 2


# Will unexpectedly materialize foo_asset
defs.get_job_def("my_graph_assets").execute_in_process(
    asset_selection=[AssetKey("baz_asset")]
)
# end_unexpected_materialization_foo
