import logging
import time
import warnings

import click
import pytest
from dagster import (
    AssetSelection,
    DailyPartitionsDefinition,
    ExperimentalWarning,
    HourlyPartitionsDefinition,
    PartitionKeyRange,
)
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor

from auto_materialize_perf_tests.partition_mappings_galore_perf_scenario import (
    partition_mappings_galore_perf_scenario,
)
from auto_materialize_perf_tests.perf_scenario import PerfScenario, RandomAssets

warnings.simplefilter("ignore", category=ExperimentalWarning)

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("dagster.auto_materialize_perf")


# ==============================================
# Scenarios
# ==============================================

unpartitioned_2000_assets = RandomAssets(
    name="giant_unpartitioned_assets", n_assets=2000, n_sources=500
)

all_daily_partitioned_500_assets = RandomAssets(
    name="large_all_daily_partitioned_assets",
    n_assets=500,
    asset_partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
)

hourly_partitions_def = HourlyPartitionsDefinition(start_date="2020-01-01-00:00")
all_hourly_partitioned_100_assets = RandomAssets(
    name="all_hourly_partitioned_100_assets",
    n_assets=100,
    asset_partitions_def=hourly_partitions_def,
)

perf_scenarios = [
    unpartitioned_2000_assets.build_scenario(max_execution_time_seconds=12),
    unpartitioned_2000_assets.build_scenario(
        n_runs=2, randomize_runs=True, max_execution_time_seconds=25
    ),
    RandomAssets(name="large_unpartitioned_assets", n_assets=500, n_sources=100).build_scenario(
        n_runs=2, randomize_runs=True, max_execution_time_seconds=5
    ),
    all_daily_partitioned_500_assets.build_scenario(
        partition_keys_to_backfill=["2020-01-01", "2020-01-02"], max_execution_time_seconds=40
    ),
    all_daily_partitioned_500_assets.build_scenario(
        partition_keys_to_backfill=[f"2020-01-{i+1:02}" for i in range(20)],
        max_execution_time_seconds=30,
    ),
    all_hourly_partitioned_100_assets.build_scenario(
        partition_keys_to_backfill=["2020-01-01-00:00", "2020-01-02-00:00"],
        max_execution_time_seconds=30,
    ),
    all_hourly_partitioned_100_assets.build_scenario(
        partition_keys_to_backfill=hourly_partitions_def.get_partition_keys_in_range(
            PartitionKeyRange("2020-01-01-00:00", "2020-01-05-03:00")
        ),
        max_execution_time_seconds=30,
    ),
    partition_mappings_galore_perf_scenario,
]


@pytest.mark.parametrize("scenario", perf_scenarios, ids=[s.name for s in perf_scenarios])
def test_auto_materialize_perf(scenario: PerfScenario):
    asset_graph = scenario.defs.get_asset_graph()
    with scenario.instance_from_snapshot() as instance:
        start = time.time()

        AssetDaemonContext(
            evaluation_id=1,
            instance=instance,
            asset_graph=asset_graph,
            cursor=AssetDaemonCursor.empty(),
            auto_materialize_asset_keys=AssetSelection.all().resolve(asset_graph),
            materialize_run_tags=None,
            auto_observe_asset_keys=set(),
            observe_run_tags=None,
            respect_materialization_data_versions=True,
            logger=logging.getLogger("dagster.amp"),
            evaluation_time=scenario.current_time,
        ).evaluate()

        end = time.time()
        execution_time_seconds = end - start
        logger.info(f"Took {execution_time_seconds} seconds")
        assert execution_time_seconds < scenario.max_execution_time_seconds


@click.group()
def perf_snapshot_command(): ...


@perf_snapshot_command.command(name="generate")
@click.argument("scenario_name", type=str, required=True)
def perf_snapshot_generate_command(scenario_name):
    if scenario_name == "all":
        selected_scenarios = perf_scenarios
    else:
        selected_scenarios = [s for s in perf_scenarios if s.name == scenario_name]

        if len(selected_scenarios) == 0:
            raise RuntimeError(
                f"No scenario with name {scenario_name}. Names: {[s.name for s in perf_scenarios]}"
            )

    for scenario in selected_scenarios:
        logger.info(f"Generating snapshot for scenario '{scenario.name}'")
        scenario.save_instance_snapshot()


@perf_snapshot_command.command(name="list")
def perf_snapshot_list_command():
    for s in perf_scenarios:
        print(s.name)  # noqa


if __name__ == "__main__":
    perf_snapshot_command()
