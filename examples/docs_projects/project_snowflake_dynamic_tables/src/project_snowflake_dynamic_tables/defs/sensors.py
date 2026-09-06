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
    asset_selection=dg.AssetSelection.assets("executive_dashboard_report"),
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
        # Network/IO failure is the one place LBYL doesn't apply — skip this tick.
        return dg.SkipReason(f"Snowflake query failed: {exc}")

    if not rows:
        return dg.SkipReason("No dynamic tables found in information_schema")

    name_to_key = {sf_name: dagster_key for dagster_key, sf_name in _TABLES}

    # Always record refresh state as observations on the virtual assets.
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

    # Snowflake owns the refresh; the dashboard must run only AFTER a refresh lands.
    # Trigger off the actual `last_completed_refresh` timestamps, never off source change.
    name_to_refresh = {row[0].upper(): row[2] for row in rows if row[0].upper() in name_to_key}
    clv_refresh = name_to_refresh.get("CUSTOMER_LIFETIME_VALUE")
    rollup_refresh = name_to_refresh.get("DAILY_REVENUE_ROLLUP")

    # Cold-start gate (LBYL): a NULL last_completed_refresh means the table has no
    # committed data yet. Firing now would read an empty table and go green on nothing.
    if clv_refresh is None or rollup_refresh is None:
        return dg.SensorResult(
            asset_events=observations,
            skip_reason="Waiting for both dynamic tables to complete a first refresh.",
            cursor=context.cursor,
        )

    # Composite run key: fire on EITHER table advancing, dedupe identical combined state.
    refresh_state = f"{clv_refresh}-{rollup_refresh}"
    if refresh_state == context.cursor:
        return dg.SensorResult(
            asset_events=observations,
            skip_reason="No dynamic table refresh since last tick.",
            cursor=context.cursor,
        )

    return dg.SensorResult(
        run_requests=[dg.RunRequest(run_key=refresh_state)],
        asset_events=observations,
        cursor=refresh_state,
    )


# end_freshness_sensor


@dg.definitions
def sensor_defs() -> dg.Definitions:
    return dg.Definitions(sensors=[dynamic_table_freshness_sensor])
