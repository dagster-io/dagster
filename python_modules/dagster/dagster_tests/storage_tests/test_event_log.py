import multiprocessing
import os
import sys
import tempfile
import traceback

import pytest
import sqlalchemy
from dagster._core.errors import DagsterEventLogInvalidForRun
from dagster._core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
    SqliteEventLogStorage,
)
from dagster._core.storage.legacy_storage import LegacyEventLogStorage
from dagster._core.storage.sql import create_engine
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage

from .utils.event_log_storage import TestEventLogStorage


class TestInMemoryEventLogStorage(TestEventLogStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def event_log_storage(self):
        storage = InMemoryEventLogStorage()
        try:
            yield storage
        finally:
            storage.dispose()


class TestSqliteEventLogStorage(TestEventLogStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def event_log_storage(self):
        # make the temp dir in the cwd since default temp roots
        # have issues with FS notif based event log watching
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            storage = SqliteEventLogStorage(tmpdir_path)
            try:
                yield storage
            finally:
                storage.dispose()

    def test_filesystem_event_log_storage_run_corrupted(self, storage):
        # URL begins sqlite:///

        with open(
            os.path.abspath(storage.conn_string_for_shard("foo")[10:]), "w", encoding="utf8"
        ) as fd:
            fd.write("some nonsense")
        with pytest.raises(sqlalchemy.exc.DatabaseError):
            storage.get_logs_for_run("foo")

    def test_filesystem_event_log_storage_run_corrupted_bad_data(self, storage):
        SqlEventLogStorageMetadata.create_all(create_engine(storage.conn_string_for_shard("foo")))
        with storage.run_connection("foo") as conn:
            event_insert = SqlEventLogStorageTable.insert().values(
                run_id="foo", event="{bar}", dagster_event_type=None, timestamp=None
            )
            conn.execute(event_insert)

        with pytest.raises(DagsterEventLogInvalidForRun):
            storage.get_logs_for_run("foo")

        SqlEventLogStorageMetadata.create_all(create_engine(storage.conn_string_for_shard("bar")))

        with storage.run_connection("bar") as conn:
            event_insert = SqlEventLogStorageTable.insert().values(
                run_id="bar", event="3", dagster_event_type=None, timestamp=None
            )
            conn.execute(event_insert)
        with pytest.raises(DagsterEventLogInvalidForRun):
            storage.get_logs_for_run("bar")

    def cmd(self, exceptions, tmpdir_path):
        storage = SqliteEventLogStorage(tmpdir_path)
        try:
            storage.get_logs_for_run("foo")
        except Exception as exc:
            exceptions.put(exc)
            exc_info = sys.exc_info()
            traceback.print_tb(exc_info[2])

    def test_concurrent_sqlite_event_log_connections(self, storage):
        tmpdir_path = storage._base_dir  # noqa: SLF001
        ctx = multiprocessing.get_context("spawn")
        exceptions = ctx.Queue()
        ps = []
        for _ in range(5):
            ps.append(ctx.Process(target=self.cmd, args=(exceptions, tmpdir_path)))
        for p in ps:
            p.start()

        j = 0
        for p in ps:
            p.join()
            j += 1

        assert j == 5

        excs = []
        while not exceptions.empty():
            excs.append(exceptions.get())
        assert not excs, excs


class TestConsolidatedSqliteEventLogStorage(TestEventLogStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def event_log_storage(self):
        # make the temp dir in the cwd since default temp roots
        # have issues with FS notif based event log watching
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            storage = ConsolidatedSqliteEventLogStorage(tmpdir_path)
            try:
                yield storage
            finally:
                storage.dispose()


class TestLegacyStorage(TestEventLogStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def event_log_storage(self):
        # make the temp dir in the cwd since default temp roots
        # have issues with FS notif based event log watching
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
            # first create the unified storage class
            storage = DagsterSqliteStorage.from_local(tmpdir_path)
            # next create the legacy adapter class
            legacy_storage = LegacyEventLogStorage(storage)
            try:
                yield legacy_storage
            finally:
                legacy_storage.dispose()
                storage.dispose()

    def is_sqlite(self, storage):
        return True
