from dagster import build_asset_reconciliation_sensor, Definitions, AssetSelection

defs = Definitions(
    assets=[airbyte_asset1, airbyte_asset2, dbt_asset1, dbt_asset2],
    sensors=[
        build_asset_reconciliation_sensor(
            asset_selection=AssetSelection.keys('dbt_asset1', 'dbt_asset2'),
            name="asset_reconciliation_sensor",
        ),
    ],
)