import tempfile
from contextlib import contextmanager

import pendulum
import pytest
from dagster import AssetKey, Output, job, op
from dagster.core.asset_defs import asset, build_assets_job
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


def test_latest_run_id_by_step_key():
    with get_instance() as instance:

        @asset
        def asset_1():
            yield Output(3)

        @asset(non_argument_deps={AssetKey("asset_1")})
        def asset_2():
            raise Exception("foo")
            yield Output(5)

        @asset(non_argument_deps={AssetKey("asset_2")})
        def asset_3():
            yield Output(7)

        many_assets_job = build_assets_job("many_assets_job", [asset_1, asset_2, asset_3])

        # Test that no run ids are fetched when many_assets_job has not been run
        latest_run_id_by_step_key = instance.get_latest_run_id_by_step_key(
            ["asset_1", "asset_2", "asset_3"]
        )
        assert latest_run_id_by_step_key == {}

        first_run_id = None
        # Test that latest run ID for all 3 assets is run ID of failing run
        result = many_assets_job.execute_in_process(instance=instance, raise_on_error=False)
        first_run_id = result.run_id
        latest_run_id_by_step_key = instance.get_latest_run_id_by_step_key(
            ["asset_1", "asset_2", "asset_3"]
        )

        assert latest_run_id_by_step_key["asset_1"] == first_run_id
        assert latest_run_id_by_step_key["asset_2"] == first_run_id
        assert latest_run_id_by_step_key["asset_3"] == first_run_id

        # Test succeeded run with only first step selected
        second_result = many_assets_job.execute_in_process(
            instance=instance, op_selection=["*asset_1"]
        )
        latest_run_id_by_step_key = instance.get_latest_run_id_by_step_key(
            ["asset_1", "asset_2", "asset_3"]
        )

        assert latest_run_id_by_step_key["asset_1"] == second_result.run_id
        assert latest_run_id_by_step_key["asset_2"] == first_run_id
        assert latest_run_id_by_step_key["asset_3"] == first_run_id
