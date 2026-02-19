"""Dynamic Tables external assets."""

import dagster as dg


@dg.asset(
    group_name="dynamic_tables",
    description="""
    Dynamic Table: Real-time sentiment aggregation (15-second refresh).

    Snowflake handles the refresh automatically.
    Dagster provides:
    - Lineage visibility (see what feeds this table)
    - Freshness monitoring (alert if refresh fails)
    - Cost tracking (via Dagster Insights)
    """,
    metadata={
        "snowflake_object": "DYNAMIC TABLE",
        "refresh_interval": "15 seconds",
        "dagster_role": "observability_only",
    },
    compute_kind="snowflake",
)
def dt_realtime_sentiment(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """External asset representing Snowflake Dynamic Table."""
    return dg.MaterializeResult(
        metadata={
            "note": dg.MetadataValue.text(
                "This is an external asset representing a Snowflake Dynamic Table. "
                "Snowflake handles the refresh automatically."
            )
        }
    )


@dg.asset(
    group_name="dynamic_tables",
    description="Dynamic Table: Hourly news aggregates",
    deps=["dt_realtime_sentiment"],
    metadata={
        "snowflake_object": "DYNAMIC TABLE",
        "refresh_interval": "1 hour",
    },
    compute_kind="snowflake",
)
def dt_hourly_aggregates(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """External asset representing Snowflake Dynamic Table."""
    return dg.MaterializeResult(
        metadata={
            "note": dg.MetadataValue.text(
                "This is an external asset representing a Snowflake Dynamic Table."
            )
        }
    )


@dg.asset(
    group_name="dynamic_tables",
    description="Dynamic Table: Daily news summary",
    deps=["dt_hourly_aggregates"],
    metadata={
        "snowflake_object": "DYNAMIC TABLE",
        "refresh_interval": "1 day",
    },
    compute_kind="snowflake",
)
def dt_daily_summary(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """External asset representing Snowflake Dynamic Table."""
    return dg.MaterializeResult(
        metadata={
            "note": dg.MetadataValue.text(
                "This is an external asset representing a Snowflake Dynamic Table."
            )
        }
    )


dynamic_table_assets = [dt_realtime_sentiment, dt_hourly_aggregates, dt_daily_summary]
