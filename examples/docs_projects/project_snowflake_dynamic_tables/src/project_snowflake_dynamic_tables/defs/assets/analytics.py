import dagster as dg
from dagster_snowflake import SnowflakeResource


# start_dashboard_asset
@dg.asset(
    group_name="analytics",
    deps=["customer_lifetime_value", "daily_revenue_rollup"],
    automation_condition=dg.AutomationCondition.eager().resolve_through_virtual(),
    kinds={"snowflake", "python"},
)
def executive_dashboard_report(
    context: dg.AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> dg.MaterializeResult:
    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                (SELECT COUNT(DISTINCT customer_id)
                 FROM ECOMMERCE.ANALYTICS.CUSTOMER_LIFETIME_VALUE)        AS total_customers,
                (SELECT SUM(revenue)
                 FROM ECOMMERCE.ANALYTICS.DAILY_REVENUE_ROLLUP
                 WHERE order_date >= DATEADD('day', -30, CURRENT_DATE())) AS total_revenue_30d
        """)
        row = cursor.fetchone()

    total_customers = int(row[0]) if row and row[0] else 0
    total_revenue = float(row[1]) if row and row[1] else 0.0

    return dg.MaterializeResult(
        metadata={
            "total_customers": dg.MetadataValue.int(total_customers),
            "total_revenue_30d": dg.MetadataValue.float(total_revenue),
        }
    )


# end_dashboard_asset


@dg.definitions
def analytics_defs() -> dg.Definitions:
    return dg.Definitions(assets=[executive_dashboard_report])
