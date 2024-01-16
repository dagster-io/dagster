from dagster import (
    AssetIn,
    Definitions,
    asset,
    define_asset_job,
    job,
    op,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG


@asset(op_tags={GLOBAL_CONCURRENCY_TAG: "foo"}, key_prefix=["prefix"])
def foo_limited_asset():
    return 1


@asset(op_tags={GLOBAL_CONCURRENCY_TAG: "bar"}, key_prefix=["prefix"])
def bar_limited_asset():
    return 1


@asset(
    op_tags={GLOBAL_CONCURRENCY_TAG: "baz"},
    key_prefix=["prefix"],
    ins={"foo_limited_asset": AssetIn(key_prefix="prefix")},
)
def baz_limited_asset_depends_on_foo(foo_limited_asset):
    return 1


concurrency_limited_asset_job = define_asset_job(
    "concurrency_limited_asset_job",
    [foo_limited_asset, bar_limited_asset, baz_limited_asset_depends_on_foo],
).resolve(
    asset_graph=AssetGraph.from_assets(
        [foo_limited_asset, bar_limited_asset, baz_limited_asset_depends_on_foo]
    )
)


@op
def foo_op(tags={GLOBAL_CONCURRENCY_TAG: "foo"}):
    return 1


@op
def bar_op(tags={GLOBAL_CONCURRENCY_TAG: "bar"}):
    return 1


@job
def partial_concurrency_limited_multi_root_job():
    foo_op()
    bar_op()


defs = Definitions(
    assets=[foo_limited_asset, bar_limited_asset, baz_limited_asset_depends_on_foo],
    jobs=[concurrency_limited_asset_job, partial_concurrency_limited_multi_root_job],
)
