import multiprocessing
import os
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import pytest
import sqlalchemy
import sqlalchemy as db
from dagster._core.errors import DagsterEventLogInvalidForRun
from dagster._core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
    SqliteEventLogStorage,
)
from dagster._core.storage.event_log.schema import ConcurrencyLimitsTable, ConcurrencySlotsTable
from dagster._core.storage.legacy_storage import LegacyEventLogStorage
from dagster._core.storage.sql import create_engine
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.storage.sqlite_storage import DagsterSqliteStorage
from dagster._utils.test import ConcurrencyEnabledSqliteTestEventLogStorage
from sqlalchemy.engine import Connection

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


def _insert_slots(conn: Connection, concurrency_key: str, num: int, delete_num: int = 0):
    rows = [
        {
            "concurrency_key": concurrency_key,
            "run_id": None,
            "step_key": None,
            "deleted": False,
        }
        for _ in range(0, num)
    ] + [
        {
            "concurrency_key": concurrency_key,
            "run_id": None,
            "step_key": None,
            "deleted": True,
        }
        for _ in range(0, delete_num)
    ]

    conn.execute(ConcurrencySlotsTable.insert().values(rows))


def _get_slot_count(conn: Connection, concurrency_key: str):
    slot_row = conn.execute(
        db_select([db.func.count(ConcurrencySlotsTable.c.id)]).where(
            db.and_(
                ConcurrencySlotsTable.c.concurrency_key == concurrency_key,
                ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
            )
        )
    ).fetchone()
    return slot_row[0] if slot_row else None


def _get_limit_row_num(conn: Connection, concurrency_key: str):
    limit_row = conn.execute(
        db_select([ConcurrencyLimitsTable.c.limit]).where(
            ConcurrencyLimitsTable.c.concurrency_key == concurrency_key
        )
    ).fetchone()
    return limit_row[0] if limit_row else None


def test_concurrency_limit_set():
    """Test that the concurrency limit is set correctly.  This doesn't really belong in the event
    log test suites, since it kind of pokes at the table internals, by querying the limit rows in
    addition to the slot rows.
    """
    TOTAL_TIMEOUT_TIME = 30
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
        storage = ConcurrencyEnabledSqliteTestEventLogStorage(base_dir=tmpdir_path)

        def _allocate_slot():
            storage.set_concurrency_slots("foo", 5)

        start = time.time()
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(_allocate_slot) for i in range(100)]
            while not all(f.done() for f in futures) and time.time() < start + TOTAL_TIMEOUT_TIME:
                time.sleep(1)

        # assert that the number of slots match the limit row
        with storage.index_connection() as conn:
            assert _get_slot_count(conn, "foo") == 5
            assert _get_limit_row_num(conn, "foo") == 5


def test_concurrency_reconcile():
    """Test that the concurrency limit is set correctly.  This doesn't really belong in the event
    log test suites, since it kind of pokes at the table internals, by querying the limit rows in
    addition to the slot rows.
    """
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir_path:
        storage = ConcurrencyEnabledSqliteTestEventLogStorage(base_dir=tmpdir_path)

        # first set up the rows based on slots
        with storage.index_connection() as conn:
            _insert_slots(conn, "foo", 5, 1)
            _insert_slots(conn, "bar", 3, 2)

            assert _get_slot_count(conn, "foo") == 5
            assert _get_slot_count(conn, "bar") == 3
            assert _get_limit_row_num(conn, "foo") is None
            assert _get_limit_row_num(conn, "bar") is None

        storage._reconcile_concurrency_limits_from_slots()  # noqa: SLF001

        with storage.index_connection() as conn:
            assert _get_slot_count(conn, "foo") == 5
            assert _get_slot_count(conn, "bar") == 3
            assert _get_limit_row_num(conn, "foo") == 5
            assert _get_limit_row_num(conn, "bar") == 3
