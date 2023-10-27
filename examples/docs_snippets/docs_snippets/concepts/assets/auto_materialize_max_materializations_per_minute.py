from dagster import AutoMaterializePolicy, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2020-10-10"),
    auto_materialize_policy=AutoMaterializePolicy.eager(
        max_materializations_per_minute=7
    ),
)
def asset1():
    ...
