from dagster import (
    AssetExecutionContext,
    Config,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    job,
    op,
    static_partitioned_config,
)

CONTINENTS = [
    "Africa",
    "Antarctica",
    "Asia",
    "Europe",
    "North America",
    "Oceania",
    "South America",
]


@asset(partitions_def=StaticPartitionsDefinition(CONTINENTS))
def continents_info(context: AssetExecutionContext):
    context.log.info(f"continent name: {context.partition_key}")


continent_job = define_asset_job("continent_job", [continents_info])
