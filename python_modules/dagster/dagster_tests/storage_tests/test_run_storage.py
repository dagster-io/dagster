import os
import tempfile
from contextlib import contextmanager

import dagster as dg
import pytest
from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.storage.legacy_storage import LegacyRunStorage
from dagster._core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage
from dagster._core.test_utils import BasicLoadingContext, environ
from dagster_test.utils.data_factory import dagster_run

from dagster_tests.storage_tests.utils.run_storage import TestRunStorage


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
        # first create the unified storage class
        storage = DagsterSqliteStorage.from_local(tempdir)
        # next create the legacy adapter class
        legacy_storage = LegacyRunStorage(storage)
        try:
            yield legacy_storage
        finally:
            storage.dispose()


class TestSqliteRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self) -> bool:
        return True

    def supports_backfill_job_name_filtering_queries(self) -> bool:
        return True

    def supports_backfill_id_filtering_queries(self) -> bool:
        return True

    def supports_backfills_count(self) -> bool:
        return True

    def supports_add_historical_run(self) -> bool:
        return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            with dg.instance_for_test(temp_dir=tmpdir_path) as instance:
                yield instance

    @pytest.fixture(name="storage", scope="function")
    def run_storage(self, instance):
        run_storage = instance.run_storage
        assert isinstance(run_storage, SqliteRunStorage)
        yield run_storage


class TestInMemoryRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self) -> bool:
        return True

    def supports_backfill_job_name_filtering_queries(self) -> bool:
        return True

    def supports_backfill_id_filtering_queries(self) -> bool:
        return True

    def supports_backfills_count(self) -> bool:
        return True

    def supports_add_historical_run(self) -> bool:
        return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with DagsterInstance.ephemeral() as the_instance:
            yield the_instance

    @pytest.fixture(name="storage")
    def run_storage(self, instance):
        yield instance.run_storage

    def test_storage_telemetry(self, storage):
        pass


class TestLegacyRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self) -> bool:
        return True

    def supports_backfill_job_name_filtering_queries(self) -> bool:
        return True

    def supports_backfill_id_filtering_queries(self) -> bool:
        return True

    def supports_backfills_count(self) -> bool:
        return True

    def supports_add_historical_run(self) -> bool:
        return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            with dg.instance_for_test(temp_dir=tmpdir_path) as instance:
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

    def test_storage_telemetry(self, storage):
        pass


@pytest.mark.asyncio
async def test_batch_run_loader():
    with dg.instance_for_test() as instance:
        context = BasicLoadingContext(instance)
        run_1 = instance.run_storage.add_run(
            dagster_run(job_name="some_pipeline", tags={"foo": "bar"})
        )
        run_2 = instance.run_storage.add_run(
            dagster_run(job_name="some_pipeline", tags={"foo": "bar"})
        )
        run_3 = instance.run_storage.add_run(
            dagster_run(job_name="some_pipeline", tags={"foo": "bar"})
        )

        records = await dg.RunRecord.gen_many(context, [run_1.run_id, run_2.run_id, run_3.run_id])
        assert records
        records = list(records)

        assert len(records) == 3
        assert check.not_none(records[0]).dagster_run.run_id == run_1.run_id
        assert check.not_none(records[1]).dagster_run.run_id == run_2.run_id
        assert check.not_none(records[2]).dagster_run.run_id == run_3.run_id

        with environ({"DAGSTER_RUN_RECORD_LOADER_BATCH_SIZE": "2"}):
            chunk_records = await dg.RunRecord.gen_many(
                context, [run_1.run_id, run_2.run_id, run_3.run_id]
            )
            assert chunk_records == records
