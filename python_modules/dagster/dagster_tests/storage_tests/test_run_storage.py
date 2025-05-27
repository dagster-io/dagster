import os
import tempfile
from contextlib import contextmanager

import pytest
from dagster import DagsterInstance
from dagster._core.storage.legacy_storage import LegacyRunStorage
from dagster._core.storage.runs import (
    InMemoryRunStorage,
    SqliteRunStorage,
    RunsFilter,
    DagsterRunStatus
)
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage
from dagster._core.test_utils import instance_for_test

from dagster_tests.storage_tests.utils.run_storage import TestRunStorage


# ----------- Context Managers -----------

@contextmanager
def create_sqlite_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)

@contextmanager
def create_in_memory_storage():
    storage = InMemoryRunStorage()
    try:
        yield storage
    finally:
        storage.dispose()

@contextmanager
def create_legacy_run_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        storage = DagsterSqliteStorage.from_local(tempdir)
        legacy_storage = LegacyRunStorage(storage)
        try:
            yield legacy_storage
        finally:
            storage.dispose()


# ----------- Latest Failed Filter Test Class -----------

class TestLatestFailedOnly(TestRunStorage):
    __test__ = True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            with instance_for_test(temp_dir=tmpdir_path) as instance:
                yield instance

    def test_latest_failed_only(self, instance):
        run_success = instance.create_run_for_pipeline(
            pipeline_name="demo_pipeline", status=DagsterRunStatus.SUCCESS
        )
        run_failed = instance.create_run_for_pipeline(
            pipeline_name="demo_pipeline", status=DagsterRunStatus.FAILURE
        )

        filtered = instance.get_run_records(
            filters=RunsFilter(
                status=[DagsterRunStatus.FAILURE],
                latest_failed_only=True
            )
        )

        assert len(filtered) == 1
        assert filtered[0].pipeline_run.run_id == run_failed.run_id


# ----------- Sqlite Run Storage Tests -----------

class TestSqliteRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self): return True
    def supports_backfill_job_name_filtering_queries(self): return True
    def supports_backfill_id_filtering_queries(self): return True
    def supports_backfills_count(self): return True
    def supports_add_historical_run(self): return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            with instance_for_test(temp_dir=tmpdir_path) as instance:
                yield instance

    @pytest.fixture(name="storage", scope="function")
    def run_storage(self, instance):
        run_storage = instance.run_storage
        assert isinstance(run_storage, SqliteRunStorage)
        yield run_storage


# ----------- In-Memory Run Storage Tests -----------

class TestInMemoryRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self): return True
    def supports_backfill_job_name_filtering_queries(self): return True
    def supports_backfill_id_filtering_queries(self): return True
    def supports_backfills_count(self): return True
    def supports_add_historical_run(self): return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with DagsterInstance.ephemeral() as the_instance:
            yield the_instance

    @pytest.fixture(name="storage")
    def run_storage(self, instance):
        yield instance.run_storage


# ----------- Legacy Run Storage Tests -----------

class TestLegacyRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self): return True
    def supports_backfill_job_name_filtering_queries(self): return True
    def supports_backfill_id_filtering_queries(self): return True
    def supports_backfills_count(self): return True
    def supports_add_historical_run(self): return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            with instance_for_test(temp_dir=tmpdir_path) as instance:
                yield instance

    @pytest.fixture(name="storage", scope="function")
    def run_storage(self, instance):
        storage = instance.get_ref().storage
        assert isinstance(storage, DagsterSqliteStorage)
        legacy_storage = LegacyRunStorage(storage)
        legacy_storage.register_instance(instance)
        try:
            yield legacy_storage
        finally:
            legacy_storage.dispose()

    def test_fetch_records_by_create_timestamp(self, storage, instance):
        run = instance.create_run_for_pipeline(pipeline_name="demo_pipeline")

        records = instance.get_run_records(
            filters=RunsFilter(run_ids=[run.run_id])
        )

        assert len(records) == 1
        assert records[0].pipeline_run.run_id == run.run_id
