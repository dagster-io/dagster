# pylint: disable=redefined-outer-name
from dagster import AssetIn, asset, build_assets_job

namespace1 = ["s3", "superdomain_1", "subdomain_1", "subsubdomain_1"]


@asset(namespace=namespace1)
def asset1():
    pass


@asset(
    namespace=["s3", "superdomain_2", "subdomain_2", "subsubdomain_2"],
    ins={"asset1": AssetIn(namespace=namespace1)},
)
def asset2(asset1):
    assert asset1 is None


long_asset_keys_job = build_assets_job("long_asset_keys_job", assets=[asset1, asset2])
