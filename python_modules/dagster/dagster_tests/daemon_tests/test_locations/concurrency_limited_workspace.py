import dagster as dg
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG


@dg.asset(pool="foo", key_prefix=["prefix"])
def foo_limited_asset():
    return 1


@dg.asset(pool="bar", key_prefix=["prefix"])
def bar_limited_asset():
    return 1


@dg.asset(
    pool="baz",
    key_prefix=["prefix"],
    ins={"foo_limited_asset": dg.AssetIn(key_prefix="prefix")},
)
def baz_limited_asset_depends_on_foo(foo_limited_asset):
    return 1


@dg.asset(pool="baz", key_prefix=["prefix"])
def baz_limited_asset():
    return 1


concurrency_limited_asset_job = dg.define_asset_job(
    "concurrency_limited_asset_job",
    [foo_limited_asset, bar_limited_asset, baz_limited_asset, baz_limited_asset_depends_on_foo],
).resolve(
    asset_graph=AssetGraph.from_assets(
        [foo_limited_asset, bar_limited_asset, baz_limited_asset_depends_on_foo, baz_limited_asset]
    )
)


@dg.op
def foo_op(tags={GLOBAL_CONCURRENCY_TAG: "foo"}):
    return 1


@dg.op
def bar_op(tags={GLOBAL_CONCURRENCY_TAG: "bar"}):
    return 1


@dg.job
def partial_concurrency_limited_multi_root_job():
    foo_op()
    bar_op()


defs = dg.Definitions(
    assets=[foo_limited_asset, bar_limited_asset, baz_limited_asset_depends_on_foo],
    jobs=[concurrency_limited_asset_job, partial_concurrency_limited_multi_root_job],
)
