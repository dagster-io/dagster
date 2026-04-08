from datetime import datetime, timezone

import dagster as dg

raw_orders = dg.AssetSpec("raw_orders", group_name="external_db")
raw_customers = dg.AssetSpec("raw_customers", group_name="external_db")


@dg.sensor(minimum_interval_seconds=60)
def db_table_update_sensor(
    context: dg.SensorEvaluationContext,
) -> dg.SensorResult:
    last_checked = float(context.cursor) if context.cursor else 0
    updated_tables = query_information_schema(last_checked)

    asset_events = [
        dg.AssetMaterialization(
            asset_key=table["table_name"],
            metadata={
                "last_altered": dg.MetadataValue.text(
                    datetime.fromtimestamp(
                        table["last_altered"], tz=timezone.utc
                    ).isoformat()
                ),
            },
        )
        for table in updated_tables
    ]

    new_cursor = (
        str(max(t["last_altered"] for t in updated_tables))
        if updated_tables
        else str(last_checked)
    )

    return dg.SensorResult(asset_events=asset_events, cursor=new_cursor)


@dg.asset(
    deps=[raw_orders, raw_customers],
    automation_condition=dg.AutomationCondition.on_cron("0 * * * *"),
)
def sales_report(): ...


@dg.asset(
    deps=[raw_orders],
    automation_condition=dg.AutomationCondition.eager(),
)
def order_metrics(): ...


def query_information_schema(since_timestamp: float) -> list:
    # In practice, this would query your database, e.g.:
    # SELECT table_name, last_altered
    # FROM information_schema.tables
    # WHERE last_altered > :since_timestamp
    ...
