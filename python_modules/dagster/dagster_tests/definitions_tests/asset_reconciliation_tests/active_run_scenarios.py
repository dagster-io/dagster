import datetime
from typing import Optional

from dagster import (
    DailyPartitionsDefinition,
    PartitionKeyRange,
)
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.time_window_partitions import HourlyPartitionsDefinition
from dagster._core.events import DagsterEvent, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._seven.compat.pendulum import create_pendulum_time

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    asset_def,
    run_request,
)

DEFAULT_JOB_NAME = "some_job"

daily_partitions_def = DailyPartitionsDefinition("2020-01-01")
hourly_partitions_def = HourlyPartitionsDefinition("2020-01-01-00:00")

assets = [
    asset_def("upstream_daily", partitions_def=daily_partitions_def),
    asset_def("downstream_daily", ["upstream_daily"], partitions_def=daily_partitions_def),
    asset_def("downstream_hourly", ["upstream_daily"], partitions_def=hourly_partitions_def),
]


def create_materialization_event_log_entry(
    asset_key: AssetKey, partition: Optional[str] = None, run_id: str = "1"
) -> EventLogEntry:
    return EventLogEntry(
        job_name=DEFAULT_JOB_NAME,
        run_id="1",
        error_info=None,
        level="INFO",
        user_message="",
        timestamp=datetime.datetime.now().timestamp(),
        dagster_event=DagsterEvent(
            event_type_value="ASSET_MATERIALIZATION",
            job_name=DEFAULT_JOB_NAME,
            event_specific_data=StepMaterializationData(
                materialization=AssetMaterialization(asset_key=asset_key, partition=partition)
            ),
        ),
    )


active_run_scenarios = {
    "downstream_still_in_progress": AssetReconciliationScenario(
        assets=assets,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2020, month=1, day=2, hour=0),
        # manually populate entries here to create an in-progress run for both daily assets
        dagster_runs=[
            DagsterRun(
                job_name=DEFAULT_JOB_NAME,
                run_id="1",
                status=DagsterRunStatus.STARTED,
                asset_selection={AssetKey("upstream_daily"), AssetKey("downstream_daily")},
                tags={"dagster/partition": "2020-01-01"},
            )
        ],
        event_log_entries=[
            create_materialization_event_log_entry(
                asset_key=AssetKey("upstream_daily"), partition="2020-01-01"
            ),
        ],
        expected_run_requests=[
            run_request(asset_keys=["downstream_hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2020-01-01-00:00", end="2020-01-01-23:00")
            )
        ],
    ),
}
