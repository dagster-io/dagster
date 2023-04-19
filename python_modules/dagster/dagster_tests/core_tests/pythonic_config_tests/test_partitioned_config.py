from dagster import (
    AssetKey,
    Config,
    DailyPartitionsDefinition,
    RunConfig,
    asset,
    daily_partitioned_config,
    define_asset_job,
)
from dagster._core.definitions.asset_graph import AssetGraph


def test_job_config_with_asset_partitions() -> None:
    daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    class AssetConfig(Config):
        a: int

    @asset(partitions_def=daily_partitions_def)
    def asset1(context, config: AssetConfig):
        assert config.a == 5
        assert context.partition_key == "2020-01-01"

    the_job = define_asset_job(
        "job",
        partitions_def=daily_partitions_def,
        config=RunConfig(ops={"asset1": AssetConfig(a=5)}),
    ).resolve(asset_graph=AssetGraph.from_assets([asset1]))

    assert the_job.execute_in_process(partition_key="2020-01-01").success
    assert (
        the_job.get_job_def_for_subset_selection(asset_selection={AssetKey("asset1")})
        .execute_in_process(partition_key="2020-01-01")
        .success
    )


def test_job_partitioned_config_with_asset_partitions() -> None:
    daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    class AssetConfig(Config):
        day_of_month: int

    @asset(partitions_def=daily_partitions_def)
    def asset1(context, config: AssetConfig):
        assert config.day_of_month == 1
        assert context.partition_key == "2020-01-01"

    @daily_partitioned_config(start_date="2020-01-01")
    def myconfig(start, _end):
        return RunConfig(ops={"asset1": AssetConfig(day_of_month=start.day)})

    the_job = define_asset_job("job", config=myconfig).resolve(
        asset_graph=AssetGraph.from_assets([asset1])
    )

    assert the_job.execute_in_process(partition_key="2020-01-01").success
