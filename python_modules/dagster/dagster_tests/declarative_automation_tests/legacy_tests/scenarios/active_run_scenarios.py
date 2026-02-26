import datetime

import dagster as dg
from dagster._core.definitions.events import AssetKey
from dagster._core.events import StepMaterializationData
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._time import create_datetime

from dagster_tests.declarative_automation_tests.scenario_utils.base_scenario import (
    AssetReconciliationScenario,
    asset_def,
    observable_source_asset_def,
    run,
    run_request,
)

DEFAULT_JOB_NAME = "some_job"

daily_partitions_def = dg.DailyPartitionsDefinition("2020-01-01")
hourly_partitions_def = dg.HourlyPartitionsDefinition("2020-01-01-00:00")

partitioned_assets = [
    asset_def("upstream_daily", partitions_def=daily_partitions_def),
    asset_def("downstream_daily", ["upstream_daily"], partitions_def=daily_partitions_def),
    asset_def("downstream_hourly", ["upstream_daily"], partitions_def=hourly_partitions_def),
]

freshness_with_observable_source_assets = [
    observable_source_asset_def("observable_source"),
    asset_def("asset0"),
    asset_def("asset1", ["observable_source", "asset0"]),
    asset_def(
        "asset2",
        ["asset1"],
        legacy_freshness_policy=dg.LegacyFreshnessPolicy(maximum_lag_minutes=30),
    ),
]


def create_materialization_event_log_entry(
    asset_key: AssetKey, partition: str | None = None, run_id: str = "1"
) -> dg.EventLogEntry:
    return dg.EventLogEntry(
        job_name=DEFAULT_JOB_NAME,
        run_id="1",
        error_info=None,
        level="INFO",
        user_message="",
        timestamp=datetime.datetime.now().timestamp(),
        dagster_event=dg.DagsterEvent(
            event_type_value="ASSET_MATERIALIZATION",
            job_name=DEFAULT_JOB_NAME,
            event_specific_data=StepMaterializationData(
                materialization=dg.AssetMaterialization(asset_key=asset_key, partition=partition)
            ),
        ),
    )


active_run_scenarios = {
    "downstream_still_in_progress": AssetReconciliationScenario(
        assets=partitioned_assets,
        unevaluated_runs=[
            run(["upstream_daily", "downstream_daily"], partition_key="2020-01-01"),
        ],
        current_time=create_datetime(year=2020, month=1, day=2, hour=0),
        # manually populate entries here to create an in-progress run for both daily assets
        dagster_runs=[
            dg.DagsterRun(
                job_name=DEFAULT_JOB_NAME,
                run_id="1",
                status=DagsterRunStatus.STARTED,
                asset_selection={dg.AssetKey("upstream_daily"), dg.AssetKey("downstream_daily")},
                tags={"dagster/partition": "2020-01-01"},
            )
        ],
        event_log_entries=[
            create_materialization_event_log_entry(
                asset_key=dg.AssetKey("upstream_daily"), partition="2020-01-01"
            ),
        ],
        expected_run_requests=[
            run_request(asset_keys=["downstream_hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                dg.PartitionKeyRange(start="2020-01-01-00:00", end="2020-01-01-23:00")
            )
        ],
    ),
    "freshness_with_observable_source_still_in_progress": AssetReconciliationScenario(
        assets=freshness_with_observable_source_assets,
        unevaluated_runs=[
            run(["observable_source"], is_observation=True),
            run(["asset0", "asset1", "asset2"]),
        ],
        current_time=create_datetime(year=2020, month=1, day=2, hour=0),
        # manually populate entries here to create an in-progress run for both downstream assets
        dagster_runs=[
            dg.DagsterRun(
                job_name=DEFAULT_JOB_NAME,
                run_id="1",
                status=DagsterRunStatus.STARTED,
                asset_selection={
                    dg.AssetKey("asset0"),
                    dg.AssetKey("asset1"),
                    dg.AssetKey("asset2"),
                },
            )
        ],
        evaluation_delta=datetime.timedelta(minutes=35),
        event_log_entries=[],
        # a run is in progress which will satisfy this policy
        expected_run_requests=[],
    ),
}
