import datetime
import time

from dagster import (
    AutomationCondition,
    DagsterInstance,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    evaluate_automation_conditions,
)
from dagster._core.definitions.automation_tick_evaluation_context import build_run_requests
from dagster._time import get_current_datetime
from dagster_test.toys.auto_materializing.large_graph import AssetLayerConfig, build_assets


def run_declarative_automation_perf_simulation(instance: DagsterInstance) -> None:
    hourly_partitions_def = HourlyPartitionsDefinition("2020-01-01-00:00")
    daily_partitions_def = DailyPartitionsDefinition("2020-01-01")
    assets = build_assets(
        id="perf_test",
        layer_configs=[
            AssetLayerConfig(50, 0, hourly_partitions_def),
            AssetLayerConfig(100, 2, hourly_partitions_def, n_checks_per_asset=1),
            AssetLayerConfig(100, 4, hourly_partitions_def, n_checks_per_asset=2),
            AssetLayerConfig(100, 4, daily_partitions_def, n_checks_per_asset=2),
            AssetLayerConfig(100, 2, daily_partitions_def),
            AssetLayerConfig(50, 2, daily_partitions_def),
        ],
        automation_condition=AutomationCondition.eager()
        & AutomationCondition.all_deps_blocking_checks_passed(),
    )
    defs = Definitions(assets=assets)
    asset_job = defs.get_implicit_global_asset_job_def()

    cursor = None
    start = time.time()
    evaluation_time = get_current_datetime() - datetime.timedelta(days=1)
    for _ in range(3):
        result = evaluate_automation_conditions(
            defs=assets, instance=instance, cursor=cursor, evaluation_time=evaluation_time
        )
        cursor = result.cursor
        end = time.time()
        duration = end - start
        # all iterations should take less than 20 seconds on this graph
        assert duration < 20.0

        # simulate the new events that would come from the requested runs
        run_requests = build_run_requests(
            entity_subsets=[r.true_subset for r in result.results],
            asset_graph=defs.get_asset_graph(),
            run_tags={},
            emit_backfills=False,
        )
        for run_request in run_requests:
            asset_job.get_subset(
                asset_selection=set(run_request.asset_selection)
                if run_request.asset_selection
                else None,
                asset_check_selection=set(run_request.asset_check_keys)
                if run_request.asset_check_keys
                else None,
            ).execute_in_process(instance=instance, partition_key=run_request.partition_key)

        evaluation_time += datetime.timedelta(hours=1)
        start = time.time()


def test_eager_perf() -> None:
    run_declarative_automation_perf_simulation(DagsterInstance.ephemeral())
