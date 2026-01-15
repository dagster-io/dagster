"""Sensor definitions for Dagster."""

from typing import TYPE_CHECKING

import dagster as dg

from dagster_snowflake_ai.defs.resources import resources

if TYPE_CHECKING:
    pass


@dg.sensor(
    minimum_interval_seconds=60,
    name="dynamic_table_freshness_sensor",
)
def dynamic_table_freshness_sensor(
    context: dg.SensorEvaluationContext,
) -> dg.SkipReason:
    """
    Monitor Dynamic Table freshness - alert if Snowflake's auto-refresh fails.

    Partnership positioning:
    - Snowflake: Handles the actual refresh (15-second latency!)
    - Dagster: Monitors, alerts, provides operational visibility
    """
    snowflake = resources["snowflake"]

    try:
        with snowflake.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    name,
                    refresh_mode,
                    TIMESTAMPDIFF(
                        'second',
                        last_refresh_time,
                        CURRENT_TIMESTAMP()
                    ) as seconds_since_refresh,
                    target_lag,
                    CASE
                        WHEN seconds_since_refresh > target_lag * 2 THEN 'STALE'
                        WHEN seconds_since_refresh > target_lag THEN 'WARNING'
                        ELSE 'FRESH'
                    END as freshness_status
                FROM information_schema.dynamic_tables
                WHERE schema_name = 'ANALYTICS'
            """)
            dynamic_table_freshness_records = cursor.fetchall()

            for table_record in dynamic_table_freshness_records:
                table_name = table_record[0]
                seconds_since_refresh = table_record[2]
                freshness_status = table_record[4] if len(table_record) > 4 else None

                if freshness_status == "STALE":
                    context.log.warning(
                        f"Dynamic Table {table_name} is stale! "
                        f"Last refresh: {seconds_since_refresh} seconds ago"
                    )

            return dg.SkipReason("Freshness check completed")
    except Exception as exc:
        context.log.warning(f"Error checking Dynamic Table freshness: {exc}")
        return dg.SkipReason(f"Error checking freshness: {exc}")
