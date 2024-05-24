from datetime import timedelta

from dagster_snowflake import SnowflakeResource, fetch_last_updated_timestamps

from dagster import (
    AssetSelection,
    AssetSpec,
    Definitions,
    EnvVar,
    MetadataValue,
    ObserveResult,
    ScheduleDefinition,
    build_last_update_freshness_checks,
    define_asset_job,
    multi_observable_source_asset,
)

TABLE_SCHEMA = "PUBLIC"
table_names = ["charges", "customers"]
asset_specs = [AssetSpec(table_name) for table_name in table_names]


@multi_observable_source_asset(specs=asset_specs)
def source_tables(snowflake: SnowflakeResource):
    with snowflake.get_connection() as conn:
        freshness_results = fetch_last_updated_timestamps(
            snowflake_connection=conn.cursor(),
            tables=table_names,
            schema=TABLE_SCHEMA,
        )
        for table_name, last_updated in freshness_results.items():
            yield ObserveResult(
                asset_key=table_name,
                metadata={
                    "dagster/last_updated_timestamp": MetadataValue.timestamp(
                        last_updated
                    )
                },
            )


source_tables_observation_schedule = ScheduleDefinition(
    job=define_asset_job(
        "source_tables_observation_job",
        selection=AssetSelection.assets(source_tables),
    ),
    # Runs every minute. Usually, a much less frequent cadence is necessary,
    # but a short cadence makes it easier to play around with this example.
    cron_schedule="* * * * *",
)


source_table_freshness_checks = build_last_update_freshness_checks(
    assets=[source_tables],
    lower_bound_delta=timedelta(hours=2),
)


defs = Definitions(
    assets=[source_tables],
    asset_checks=source_table_freshness_checks,
    schedules=[source_tables_observation_schedule],
    resources={
        "snowflake": SnowflakeResource(
            user=EnvVar("SNOWFLAKE_USER"),
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
        )
    },
)
