from dagster import (
    asset,
    build_asset_reconciliation_sensor,
    Definitions,
    AssetSelection,
)


@asset
def airbyte_asset1():
    pass


@asset
def airbyte_asset2():
    pass


@asset
def dbt_asset2():
    pass


@asset
def dbt_asset1():
    pass


# airbyte_dbt_sensor_start

defs = Definitions(
    assets=[airbyte_asset1, airbyte_asset2, dbt_asset1, dbt_asset2],
    sensors=[
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.keys("dbt_asset1", "dbt_asset2"),
            name="asset_reconciliation_sensor",
        ),
    ],
)

# airbyte_dbt_sensor_end
