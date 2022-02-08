from dagster import AssetKey, schedule, sensor
from dagster.core.asset_defs import AssetCollection, AssetIn, asset


@asset
def asset_foo():
    return "foo"


@asset
def asset_bar():
    return "bar"


@asset(
    ins={"bar_in": AssetIn(asset_key=AssetKey("asset_foo"))}
)  # should still use output from asset_foo
def last_asset(bar_in):
    return bar_in


asset_lst = [last_asset, asset_bar, asset_foo]
collection = AssetCollection.from_list(assets=asset_lst)


@sensor(
    job=collection.build_job(),
)
def full_collection_sensor():
    pass


@schedule(cron_schedule="* * * * *", job=collection.build_job(name="partial", subset="asset_foo"))
def subset_schedule():
    pass
