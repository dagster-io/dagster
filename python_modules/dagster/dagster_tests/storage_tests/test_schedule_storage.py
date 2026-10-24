import tempfile
from contextlib import contextmanager
from unittest import mock

import pytest
import sqlalchemy as db
from dagster._core.storage.legacy_storage import LegacyScheduleStorage
from dagster._core.storage.schedules import SqliteScheduleStorage
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage
from dagster._utils.test.schedule_storage import TestScheduleStorage


@contextmanager
def create_sqlite_schedule_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        yield SqliteScheduleStorage.from_local(tempdir)


@contextmanager
def create_legacy_schedule_storage():
    with tempfile.TemporaryDirectory() as tempdir:
        # first create the unified storage class
        storage = DagsterSqliteStorage.from_local(tempdir)
        # next create the legacy adapter class
        legacy_storage = LegacyScheduleStorage(storage)
        try:
            yield legacy_storage
        finally:
            legacy_storage.dispose()
            storage.dispose()


class TestSqliteScheduleStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_sqlite_schedule_storage])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s

    def test_bucket_gating(self, storage):
        with mock.patch(
            "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.7.17",
        ):
            assert not storage.supports_batch_queries

        with mock.patch(
            "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.25.1",
        ):
            assert storage.supports_batch_queries

        with mock.patch(
            "dagster._core.storage.schedules.sqlite.sqlite_schedule_storage.get_sqlite_version",
            return_value="3.25.19",
        ):
            assert storage.supports_batch_queries


CREATE_TIMESTAMP_INDEX = "idx_asset_daemon_asset_evaluations_create_timestamp"
# Alembic head immediately before the create_timestamp index migration.
PRE_CREATE_TIMESTAMP_INDEX_REVISION = "29b539ebc72a"


def _asset_evaluations_index_names(storage: SqliteScheduleStorage) -> set[str | None]:
    with storage.connect() as conn:
        return {
            index.get("name")
            for index in db.inspect(conn).get_indexes("asset_daemon_asset_evaluations")
        }


def test_asset_evaluations_create_timestamp_index_on_fresh_db() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        storage = SqliteScheduleStorage.from_local(tempdir)
        try:
            assert CREATE_TIMESTAMP_INDEX in _asset_evaluations_index_names(storage)
        finally:
            storage.dispose()


def test_asset_evaluations_create_timestamp_index_added_by_upgrade() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        storage = SqliteScheduleStorage.from_local(tempdir)
        try:
            # Simulate a database created before the index existed.
            with storage.connect() as conn:
                conn.execute(db.text(f"DROP INDEX IF EXISTS {CREATE_TIMESTAMP_INDEX}"))
                conn.execute(
                    db.text("UPDATE alembic_version SET version_num = :rev"),
                    {"rev": PRE_CREATE_TIMESTAMP_INDEX_REVISION},
                )
            assert CREATE_TIMESTAMP_INDEX not in _asset_evaluations_index_names(storage)

            storage.upgrade()

            assert CREATE_TIMESTAMP_INDEX in _asset_evaluations_index_names(storage)
        finally:
            storage.dispose()


class TestLegacyStorage(TestScheduleStorage):
    __test__ = True

    @pytest.fixture(name="storage", params=[create_legacy_schedule_storage])
    def schedule_storage(self, request):
        with request.param() as s:
            yield s
