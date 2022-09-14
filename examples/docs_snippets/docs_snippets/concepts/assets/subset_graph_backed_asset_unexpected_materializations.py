from dagster import AssetKey, Out, op

from .subset_graph_backed_asset import my_repo


# start_unexpected_materialization_foo
@op(out={"foo_1": Out(), "foo_2": Out()})
def foo():
    return 1, 2


# Will unexpectedly materialize foo_asset
my_repo.get_job("graph_asset").execute_in_process(
    asset_selection=[AssetKey("baz_asset")]
)
# end_unexpected_materialization_foo
