from dagster import (
    AssetSelection,
    Definitions,
    FreshnessPolicy,
    asset,
    build_asset_reconciliation_sensor, 
    materialize
)

# declare_schedule_start

@asset
def transactions():
    pass

@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=60, cron_schedule="0 9 * * *"))
def sales(transactions):
    pass

@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=120))
def expenses(transactions):
    pass

update_sensor = build_asset_reconciliation_sensor(
    name="update_sensor", asset_selection=AssetSelection.all()
)

defs = Definitions(assets=[transactions, sales, expenses], sensors=[update_sensor])

# declare_schedule_end

def test_declare_sensor():
    assert defs.get_sensor_def('update_sensor')

def test_assets():
    result= materialize([transactions, expenses, sales])
    assert result.success

