import tempfile
from contextlib import contextmanager

import pendulum
import pytest
from dagster import job, op
from dagster.core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import InMemoryEventLogStorage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster_tests.core_tests.storage_tests.utils.run_storage import TestRunStorage


@contextmanager
def create_sqlite_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)


@contextmanager
def create_in_memory_storage():
    yield InMemoryRunStorage()


class TestSqliteImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_sqlite_run_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s


class TestInMemoryImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_in_memory_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    def test_storage_telemetry(self, storage):
        pass


@contextmanager
def get_instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=SqliteRunStorage.from_local(temp_dir),
            event_storage=InMemoryEventLogStorage(),
            compute_log_manager=NoOpComputeLogManager(),
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=SyncInMemoryRunLauncher(),
        )


@op
def a():
    pass


@job
def my_job():
    a()


def test_run_record_timestamps():
    with get_instance() as instance:
        freeze_datetime = to_timezone(
            create_pendulum_time(2019, 11, 2, 0, 0, 0, tz="US/Central"), "US/Pacific"
        )

        with pendulum.test(freeze_datetime):
            result = my_job.execute_in_process(instance=instance)
            records = instance.get_run_records(filters=PipelineRunsFilter(run_ids=[result.run_id]))
            assert len(records) == 1
            record = records[0]
            assert record.start_time == 1572670800.0
            assert record.end_time == 1572670800.0
