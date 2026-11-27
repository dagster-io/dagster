"""Shared pieces of the backfill load tests: instance, workspace, launcher and run simulator.

The run launcher and run workers are replaced by in-process fakes so that the measured cost is
that of the daemons and storage, not of executing runs. To set up load quickly, runs are written
and updated with direct statements against the run storage tables, which relies on the private
`SqlRunStorage.connect` and schema: the daemons under test only use public storage methods.
"""

import argparse
import logging
import sys
import time
import uuid
from collections import deque
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any

import dagster as dg
import dagster._check as check
from dagster._core.definitions.repository_definition.valid_definitions import (
    SINGLETON_REPOSITORY_NAME,
)
from dagster._core.events import DagsterEvent, DagsterEventType, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.launcher import LaunchRunContext, RunLauncher
from dagster._core.remote_origin import (
    InProcessCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.runs import SqlRunStorage
from dagster._core.storage.runs.schema import RunsTable, RunTagsTable
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
    environ,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._serdes import ConfigurableClass, ConfigurableClassData, serialize_value
from dagster._time import get_current_datetime

LOCATION_NAME = "backfill_load"
JOB_NAME = "load_test_job"
INSERT_BATCH_SIZE = 5000
EVENT_BATCH_SIZE = 1000


class NoopRunLauncher(RunLauncher, ConfigurableClass):
    """Accepts every launch without doing anything: the run stays STARTING until the simulator
    picks it up.
    """

    def __init__(self, inst_data: ConfigurableClassData | None = None):
        self._inst_data = inst_data
        super().__init__()

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls) -> Mapping[str, Any]:
        return {}

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]):
        return cls(inst_data=inst_data)

    def launch_run(self, context: LaunchRunContext) -> None:
        pass

    def terminate(self, run_id: str) -> bool:
        return True


def add_storage_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--postgres-url",
        help="Postgres database to use, which is wiped. Defaults to a temporary sqlite instance.",
    )
    parser.add_argument(
        "--pool-size",
        type=int,
        help=(
            "Postgres connections kept open per storage, set as `storage.postgres.pool`. Requires"
            " a dagster-postgres version that supports pooling. Defaults to no pooling."
        ),
    )


def storage_config(postgres_url: str | None, pool_size: int | None) -> dict[str, Any]:
    """Instance storage overrides. `pool_size` sets `storage.postgres.pool`, which must be
    supported by the dagster-postgres version under test.
    """
    if not postgres_url:
        check.invariant(pool_size is None, "--pool-size requires --postgres-url")
        return {}
    config: dict[str, Any] = {"postgres_url": postgres_url}
    if pool_size is not None:
        config["pool"] = {"pool_size": pool_size, "max_overflow": 0}
    return {"storage": {"postgres": config}}


@contextmanager
def load_test_instance(
    postgres_url: str | None,
    pool_size: int | None = None,
    run_queue_config: Mapping[str, Any] | None = None,
) -> Iterator[dg.DagsterInstance]:
    """A wiped instance with the queued run coordinator and the no-op launcher. Wiping deletes
    every run, event and backfill in the postgres database, if any.
    """
    overrides = {
        **storage_config(postgres_url, pool_size),
        "run_launcher": {"module": __name__, "class": NoopRunLauncher.__name__},
        "run_coordinator": {
            "module": "dagster._core.run_coordinator",
            "class": "QueuedRunCoordinator",
            "config": {"max_concurrent_runs": -1, **(run_queue_config or {})},
        },
        "telemetry": {"enabled": False},
    }
    with instance_for_test(overrides=overrides) as instance:
        instance.wipe()
        yield instance


@contextmanager
def load_test_workspace(
    instance: dg.DagsterInstance,
    num_assets: int,
    num_partitions: int,
    backfill_policy: str,
    num_large_partitions: int = 0,
) -> Iterator[WorkspaceProcessContext]:
    """A workspace with the `definitions` code location loaded in process."""
    target = InProcessTestWorkspaceLoadTarget(
        InProcessCodeLocationOrigin(
            LoadableTargetOrigin(
                executable_path=sys.executable,
                module_name="dagster_test.benchmarks.backfill_load.definitions",
            ),
            location_name=LOCATION_NAME,
        )
    )
    with (
        environ(
            {
                "BACKFILL_LOAD_NUM_ASSETS": str(num_assets),
                "BACKFILL_LOAD_NUM_PARTITIONS": str(num_partitions),
                "BACKFILL_LOAD_NUM_LARGE_PARTITIONS": str(num_large_partitions),
                "BACKFILL_LOAD_BACKFILL_POLICY": backfill_policy,
            }
        ),
        create_test_daemon_workspace_context(target, instance) as context,
    ):
        entry = context.create_request_context().get_code_location_entries()[LOCATION_NAME]
        if not entry.code_location:
            raise Exception(f"Failed to load the load test code location: {entry.load_error}")
        yield context


def _run_storage(instance: dg.DagsterInstance) -> SqlRunStorage:
    return check.inst(instance.run_storage, SqlRunStorage)


def _job_origin() -> RemoteJobOrigin:
    """An origin for runs that are inserted directly. The job does not exist in any workspace."""
    return RemoteJobOrigin(
        RemoteRepositoryOrigin(
            InProcessCodeLocationOrigin(
                LoadableTargetOrigin(executable_path=sys.executable), location_name=LOCATION_NAME
            ),
            SINGLETON_REPOSITORY_NAME,
        ),
        JOB_NAME,
    )


def bulk_insert_runs(
    instance: dg.DagsterInstance,
    num_runs: int,
    status: DagsterRunStatus,
    tags: Mapping[str, str],
) -> None:
    """Inserts runs straight into the run storage tables, bypassing the instance for speed."""
    origin = _job_origin()
    now = get_current_datetime()
    start_time = time.time() if status == DagsterRunStatus.STARTED else None
    rows, tag_rows = [], []
    for _ in range(num_runs):
        run = DagsterRun(
            job_name=JOB_NAME,
            run_id=str(uuid.uuid4()),
            status=status,
            tags=tags,
            remote_job_origin=origin,
        )
        rows.append(
            dict(
                run_id=run.run_id,
                pipeline_name=run.job_name,
                status=status.value,
                run_body=serialize_value(run),
                backfill_id=tags.get(BACKFILL_ID_TAG),
                create_timestamp=now,
                update_timestamp=now,
                start_time=start_time,
            )
        )
        tag_rows += [dict(run_id=run.run_id, key=k, value=v) for k, v in tags.items()]
    with _run_storage(instance).connect() as conn:
        for i in range(0, len(rows), INSERT_BATCH_SIZE):
            conn.execute(RunsTable.insert(), rows[i : i + INSERT_BATCH_SIZE])
        for i in range(0, len(tag_rows), INSERT_BATCH_SIZE):
            conn.execute(RunTagsTable.insert(), tag_rows[i : i + INSERT_BATCH_SIZE])


def _bulk_set_status(
    instance: dg.DagsterInstance, runs: Sequence[DagsterRun], status: DagsterRunStatus
) -> None:
    """Sets the status of runs in the run storage tables, without storing run events."""
    now = get_current_datetime()
    time_column = "start_time" if status == DagsterRunStatus.STARTED else "end_time"
    with _run_storage(instance).connect() as conn:
        for run in runs:
            conn.execute(
                RunsTable.update()
                .where(RunsTable.c.run_id == run.run_id)
                .values(
                    status=status.value,
                    run_body=serialize_value(run.with_status(status)),
                    update_timestamp=now,
                    **{time_column: now.timestamp()},
                )
            )


def _materialization(run: DagsterRun, asset_key: dg.AssetKey, partition: str | None):
    return EventLogEntry(
        user_message="",
        level=logging.INFO,
        job_name=run.job_name,
        run_id=run.run_id,
        error_info=None,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            event_type_value=DagsterEventType.ASSET_MATERIALIZATION.value,
            job_name=run.job_name,
            event_specific_data=StepMaterializationData(
                dg.AssetMaterialization(asset_key=asset_key, partition=partition)
            ),
        ),
    )


class RunSimulator:
    """Stands in for run workers. Each step moves launched (STARTING) runs to STARTED, and
    completes runs that have been started for at least `run_duration` seconds: it stores a
    materialization for each asset partition that the run targets, then marks the run successful.
    Runs never fail.
    """

    def __init__(
        self,
        instance: dg.DagsterInstance,
        partitions_def: dg.PartitionsDefinition,
        run_duration: float = 0.0,
    ):
        self._instance = instance
        # Partition ranges are expanded with this definition, which only needs to contain them
        self._partitions_def = partitions_def
        self._run_duration = run_duration
        self._started: deque[tuple[float, DagsterRun]] = deque()

    def _partition_keys(self, run: DagsterRun) -> Sequence[str | None]:
        if PARTITION_NAME_TAG in run.tags:
            return [run.tags[PARTITION_NAME_TAG]]
        if ASSET_PARTITION_RANGE_START_TAG in run.tags:
            return self._partitions_def.get_partition_keys_in_range(
                dg.PartitionKeyRange(
                    run.tags[ASSET_PARTITION_RANGE_START_TAG],
                    run.tags[ASSET_PARTITION_RANGE_END_TAG],
                )
            )
        return [None]

    @property
    def num_running(self) -> int:
        return len(self._started)

    def step(self) -> tuple[int, int]:
        """Returns the number of runs started and completed."""
        now = time.time()
        starting = self._instance.get_runs(RunsFilter(statuses=[DagsterRunStatus.STARTING]))
        _bulk_set_status(self._instance, starting, DagsterRunStatus.STARTED)
        self._started.extend((now, run) for run in starting)

        completed: list[DagsterRun] = []
        while self._started and self._started[0][0] + self._run_duration <= now:
            completed.append(self._started.popleft()[1])
        events = [
            _materialization(run, asset_key, partition_key)
            for run in completed
            for asset_key in run.asset_selection or []
            for partition_key in self._partition_keys(run)
        ]
        for i in range(0, len(events), EVENT_BATCH_SIZE):
            self._instance.event_log_storage.store_event_batch(events[i : i + EVENT_BATCH_SIZE])
        _bulk_set_status(self._instance, completed, DagsterRunStatus.SUCCESS)
        return len(starting), len(completed)
