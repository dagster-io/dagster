import dagster as dg
from dagster_snowflake import SnowflakeResource

# start_dynamic_table_specs
customer_lifetime_value = dg.AssetSpec(
    key="customer_lifetime_value",
    group_name="dynamic_tables",
    description=(
        "Snowflake Dynamic Table: per-customer lifetime value computed from orders.\n\n"
        "TARGET_LAG = '1 minute', REFRESH_MODE = INCREMENTAL.\n"
        "Snowflake refreshes this automatically — Dagster provides lineage and monitoring."
    ),
    deps=["raw_orders", "raw_customers"],
    is_virtual=True,
    metadata={
        "snowflake_object_type": "DYNAMIC TABLE",
        "target_lag": "1 minute",
        "refresh_mode": "INCREMENTAL",
        "snowflake_table": "ECOMMERCE.ANALYTICS.CUSTOMER_LIFETIME_VALUE",
    },
    kinds={"snowflake"},
)

daily_revenue_rollup = dg.AssetSpec(
    key="daily_revenue_rollup",
    group_name="dynamic_tables",
    description=(
        "Snowflake Dynamic Table: daily revenue aggregated from raw orders.\n\n"
        "TARGET_LAG = '1 hour', REFRESH_MODE = FULL.\n"
        "Snowflake refreshes this automatically — Dagster provides lineage and monitoring."
    ),
    deps=["raw_orders"],
    is_virtual=True,
    metadata={
        "snowflake_object_type": "DYNAMIC TABLE",
        "target_lag": "1 hour",
        "refresh_mode": "FULL",
        "snowflake_table": "ECOMMERCE.ANALYTICS.DAILY_REVENUE_ROLLUP",
    },
    kinds={"snowflake"},
)


# end_dynamic_table_specs


# start_freshness_checks
@dg.asset_check(asset="customer_lifetime_value")
def customer_lifetime_value_is_fresh(snowflake: SnowflakeResource) -> dg.AssetCheckResult:
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT scheduling_state, last_completed_refresh
            FROM information_schema.dynamic_tables
            WHERE UPPER(name) = 'CUSTOMER_LIFETIME_VALUE' AND schema_name = 'ANALYTICS'
        """)
        row = cursor.fetchone()
    if not row:
        return dg.AssetCheckResult(passed=False, metadata={"error": "table not found"})
    state, last_refresh = row
    return dg.AssetCheckResult(
        passed=state in ("RUNNING", "SUSPENDED"),
        metadata={
            "scheduling_state": dg.MetadataValue.text(str(state)),
            "last_completed_refresh": dg.MetadataValue.text(str(last_refresh)),
        },
    )


@dg.asset_check(asset="daily_revenue_rollup")
def daily_revenue_rollup_is_fresh(snowflake: SnowflakeResource) -> dg.AssetCheckResult:
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT scheduling_state, last_completed_refresh
            FROM information_schema.dynamic_tables
            WHERE UPPER(name) = 'DAILY_REVENUE_ROLLUP' AND schema_name = 'ANALYTICS'
        """)
        row = cursor.fetchone()
    if not row:
        return dg.AssetCheckResult(passed=False, metadata={"error": "table not found"})
    state, last_refresh = row
    return dg.AssetCheckResult(
        passed=state in ("RUNNING", "SUSPENDED"),
        metadata={
            "scheduling_state": dg.MetadataValue.text(str(state)),
            "last_completed_refresh": dg.MetadataValue.text(str(last_refresh)),
        },
    )


# end_freshness_checks


@dg.definitions
def dynamic_table_defs() -> dg.Definitions:
    return dg.Definitions(
        assets=[customer_lifetime_value, daily_revenue_rollup],
        asset_checks=[customer_lifetime_value_is_fresh, daily_revenue_rollup_is_fresh],
    )
