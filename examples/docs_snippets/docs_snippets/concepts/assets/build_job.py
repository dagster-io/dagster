# pylint: disable=redefined-outer-name
# start_marker
from dagster import AssetGroup, asset


@asset
def upstream():
    return [1, 2, 3]


@asset
def downstream_1(upstream):
    return upstream + [4]


@asset
def downstream_2(upstream):
    return len(upstream)


asset_group = AssetGroup([upstream, downstream_1, downstream_2])

all_assets = asset_group.build_job(name="my_asset_job")

downstream_assets = asset_group.build_job(
    name="my_asset_job", selection=["upstream", "downstream_1"]
)

upstream_and_downstream_1 = asset_group.build_job(
    name="my_asset_job", selection="*downstream_1"
)
# end_marker
