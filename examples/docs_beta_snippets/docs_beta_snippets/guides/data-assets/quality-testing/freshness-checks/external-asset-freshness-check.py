from datetime import timedelta

import dagster_snowflake as dg_snowflake

import dagster as dg


@dg.observable_source_asset(specs=[dg.AssetSpec("hourly_sales")])
def hourly_sales(snowflake: dg_snowflake.SnowflakeResource):
    with snowflake.get_connection() as conn:
        freshness_results = dg_snowflake.fetch_last_updated_timestamps(
            snowflake_connection=conn.cursor(),
            tables=["hourly_sales"],
            schema="PUBLIC",
        )
        for table_name, last_updated in freshness_results.items():
            yield dg.ObserveResult(
                asset_key=table_name,
                metadata={
                    "dagster/last_updated_timestamp": dg.MetadataValue.timestamp(
                        last_updated
                    )
                },
            )


freshness_check_schedule = dg.ScheduleDefinition(
    job=dg.define_asset_job(
        "hourly_sales_observation_job",
        selection=dg.AssetSelection.assets(hourly_sales),
    ),
    # Runs every minute. Usually, a much less frequent cadence is necessary,
    # but a short cadence makes it easier to play around with this example.
    cron_schedule="* * * * *",
)


hourly_sales_freshness_check = dg.build_last_update_freshness_checks(
    assets=[hourly_sales],
    lower_bound_delta=timedelta(hours=1),
)


defs = dg.Definitions(
    assets=[hourly_sales],
    asset_checks=hourly_sales_freshness_check,
    schedules=[freshness_check_schedule],
    resources={
        "snowflake": dg_snowflake.SnowflakeResource(
            user=dg.EnvVar("SNOWFLAKE_USER"),
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
        )
    },
)
