from dagster import (
    AssetSpec,
    Definitions,
    ObserveResult,
    asset,
    define_asset_job,
    multi_asset,
)


@multi_asset(specs=[AssetSpec("one"), AssetSpec("two")])
def johann():
    return [
        ObserveResult(
            asset_key="one",
            metadata={"one": 1},
        ),
        ObserveResult(
            asset_key="two",
            metadata={"two": 2},
        ),
    ]


@asset
def my_asset(one):
    return one


my_job = define_asset_job("my_job", [my_asset])

defs = Definitions(jobs=[my_job], assets=[johann, my_asset])
