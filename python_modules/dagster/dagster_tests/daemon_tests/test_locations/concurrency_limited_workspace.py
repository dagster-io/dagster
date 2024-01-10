from dagster import (
    Definitions,
    asset,
    define_asset_job,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG


@asset(op_tags={GLOBAL_CONCURRENCY_TAG: "foo"})
def concurrency_limited_asset():
    return 1


concurrency_limited_asset_job = define_asset_job(
    "concurrency_limited_asset_job", [concurrency_limited_asset]
).resolve(asset_graph=AssetGraph.from_assets([concurrency_limited_asset]))

defs = Definitions(assets=[concurrency_limited_asset], jobs=[concurrency_limited_asset_job])
