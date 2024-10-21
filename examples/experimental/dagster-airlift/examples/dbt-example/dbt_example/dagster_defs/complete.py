from dagster import Definitions, ScheduleDefinition

from dbt_example.dagster_defs.lakehouse import lakehouse_assets_def, lakehouse_existence_check
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS

from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource

daily_schedule = ScheduleDefinition(name="daily_schedule", cron_schedule="0 0 * * *", target="*")

defs = Definitions(
    assets=[
        lakehouse_assets_def(csv_path=CSV_PATH, duckdb_path=DB_PATH, columns=IRIS_COLUMNS),
        jaffle_shop_assets,
    ],
    asset_checks=[lakehouse_existence_check(csv_path=CSV_PATH, duckdb_path=DB_PATH)],
    schedules=[daily_schedule],
    resources={"dbt": jaffle_shop_resource()},
)
