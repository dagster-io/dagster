from dagster import (
    AutoMaterializePolicy,
    Definitions,
    asset,
    load_assets_from_current_module,
)


@asset
def asset1():
    ...


@asset(deps=[asset1])
def asset2():
    ...


defs = Definitions(
    assets=load_assets_from_current_module(
        auto_materialize_policy=AutoMaterializePolicy.eager(),
    )
)
