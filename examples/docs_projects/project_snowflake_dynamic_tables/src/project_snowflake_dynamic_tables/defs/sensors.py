import dagster as dg
from dagster_snowflake import SnowflakeResource

_TABLES: list[tuple[str, str]] = [
    ("customer_lifetime_value", "CUSTOMER_LIFETIME_VALUE"),
    ("daily_revenue_rollup", "DAILY_REVENUE_ROLLUP"),
]


# start_freshness_sensor
@dg.sensor(
    name="dynamic_table_freshness_sensor",
    minimum_interval_seconds=60,
)
def dynamic_table_freshness_sensor(
    context: dg.SensorEvaluationContext,
    snowflake: SnowflakeResource,
) -> dg.SensorResult | dg.SkipReason:
    table_names_sql = ", ".join(f"'{sf_name}'" for _, sf_name in _TABLES)

    try:
        with snowflake.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    name,
                    scheduling_state,
                    last_completed_refresh,
                    TIMESTAMPDIFF('second', last_completed_refresh, CURRENT_TIMESTAMP())
                        AS seconds_since_refresh
                FROM information_schema.dynamic_tables
                WHERE UPPER(name) IN ({table_names_sql})
                  AND schema_name = 'ANALYTICS'
                """
            )
            rows = cursor.fetchall()
    except Exception as exc:
        return dg.SkipReason(f"Snowflake query failed: {exc}")

    if not rows:
        return dg.SkipReason("No dynamic tables found in information_schema")

    name_to_key = {sf_name: dagster_key for dagster_key, sf_name in _TABLES}

    observations = [
        dg.AssetObservation(
            asset_key=dg.AssetKey(name_to_key[row[0].upper()]),
            metadata={
                "scheduling_state": dg.MetadataValue.text(str(row[1])),
                "last_completed_refresh": dg.MetadataValue.text(str(row[2])),
                "seconds_since_refresh": dg.MetadataValue.int(int(row[3] or 0)),
            },
        )
        for row in rows
        if row[0].upper() in name_to_key
    ]

    return dg.SensorResult(asset_events=observations, skip_reason="Freshness metadata updated.")


# end_freshness_sensor


@dg.definitions
def sensor_defs() -> dg.Definitions:
    return dg.Definitions(sensors=[dynamic_table_freshness_sensor])
