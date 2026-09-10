"""Concurrency tests against a real server.

The rest of the suite drives one storage object at a time. A dagster deployment does not:
the webserver, the daemon and every code location hold their own storage objects against
the same database, and they contend on exactly the paths SQL Server implements differently
from Postgres -- ``MERGE`` in place of an upsert, and pessimistic locking in place of MVCC.

Each test here uses *separate* storage instances rather than threads sharing one, because
sharing one shares its engine and its pool, which is not the situation being tested.
"""

import sys
import threading
import time
from collections.abc import Callable

import pytest
import sqlalchemy as db
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.events import DagsterEvent, DagsterEventType, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.remote_origin import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorType,
    SensorInstigatorData,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._daemon.types import DaemonHeartbeat
from dagster._time import get_current_timestamp
from dagster_mssql.event_log import MSSQLEventLogStorage
from dagster_mssql.run_storage import MSSQLRunStorage
from dagster_mssql.schedule_storage import MSSQLScheduleStorage


def _fake_repo_target() -> RemoteRepositoryOrigin:
    """Matches the fixture dagster's own shared schedule storage suite uses."""
    return RemoteRepositoryOrigin(
        ManagedGrpcPythonEnvCodeLocationOrigin(
            LoadableTargetOrigin(
                executable_path=sys.executable, module_name="fake", attribute="fake"
            ),
        ),
        "fake_repo_name",
    )


WORKERS = 6
ITERATIONS = 8


def run_concurrently(worker: Callable[[int], None], count: int = WORKERS) -> list[BaseException]:
    """Run `worker(i)` on `count` threads, collecting whatever they raise."""
    errors: list[BaseException] = []
    lock = threading.Lock()
    barrier = threading.Barrier(count)

    def target(index: int) -> None:
        try:
            barrier.wait()  # maximise overlap rather than letting thread 0 finish first
            worker(index)
        except BaseException as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=target, args=(i,)) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return errors


@pytest.fixture
def clean_run_storage(conn_string):
    return MSSQLRunStorage.create_clean_storage(conn_string)


@pytest.fixture
def clean_schedule_storage(conn_string):
    return MSSQLScheduleStorage.create_clean_storage(conn_string)


class TestDaemonHeartbeats:
    """`add_daemon_heartbeat` is a MERGE on `daemon_type`, written on a timer by every
    running daemon. It is the most frequently contended upsert in a deployment.
    """

    def test_same_daemon_type_from_independent_storages(self, clean_run_storage, conn_string):
        """Every worker upserts the same key, which is the worst case for the MERGE.

        Without HOLDLOCK two sessions both miss on the match and both insert, which
        surfaces as a duplicate key violation on `daemon_heartbeats.daemon_type`.
        """
        storages = [MSSQLRunStorage(conn_string) for _ in range(WORKERS)]

        def worker(index: int) -> None:
            for i in range(ITERATIONS):
                storages[index].add_daemon_heartbeat(
                    DaemonHeartbeat(
                        timestamp=get_current_timestamp(),
                        daemon_type="SENSOR",
                        daemon_id=f"worker-{index}-{i}",
                        errors=[],
                    )
                )

        errors = run_concurrently(worker)
        assert not errors, f"concurrent heartbeat upserts failed: {errors[:3]!r}"

        heartbeats = clean_run_storage.get_daemon_heartbeats()
        assert set(heartbeats) == {"SENSOR"}, "the upsert should have left exactly one row"

    def test_distinct_daemon_types(self, clean_run_storage, conn_string):
        """Different keys must not serialise against each other.

        HOLDLOCK takes a range lock on the probed key. If that range were the whole table,
        unrelated daemons would block one another -- correct, but a bottleneck.
        """
        storages = [MSSQLRunStorage(conn_string) for _ in range(WORKERS)]

        def worker(index: int) -> None:
            for i in range(ITERATIONS):
                storages[index].add_daemon_heartbeat(
                    DaemonHeartbeat(
                        timestamp=get_current_timestamp(),
                        daemon_type=f"DAEMON_{index}",
                        daemon_id=f"worker-{index}-{i}",
                        errors=[],
                    )
                )

        errors = run_concurrently(worker)
        assert not errors, f"concurrent heartbeat upserts failed: {errors[:3]!r}"
        assert set(clean_run_storage.get_daemon_heartbeats()) == {
            f"DAEMON_{i}" for i in range(WORKERS)
        }


class TestCursorValues:
    """`set_cursor_values` is a multi-row MERGE, so it can hold range locks on several
    keys at once -- the shape most likely to deadlock if locks are taken in varying order.
    """

    def test_overlapping_key_sets_in_different_orders(self, clean_run_storage, conn_string):
        storages = [MSSQLRunStorage(conn_string) for _ in range(WORKERS)]
        keys = [f"cursor_{i}" for i in range(5)]

        def worker(index: int) -> None:
            # rotate the key order per worker: if the MERGE acquired locks in the order the
            # rows are given, workers would take them in conflicting orders and deadlock
            ordered = keys[index % len(keys) :] + keys[: index % len(keys)]
            for i in range(ITERATIONS):
                storages[index].set_cursor_values({k: f"{index}-{i}" for k in ordered})

        errors = run_concurrently(worker)
        assert not errors, f"concurrent multi-row upserts failed: {errors[:3]!r}"
        assert set(clean_run_storage.get_cursor_values(set(keys))) == set(keys)


class TestInstigatorState:
    """`_add_or_update_instigators_table` is a MERGE the daemon runs for every sensor and
    schedule on each tick.
    """

    def test_same_selector_from_independent_storages(self, clean_schedule_storage, conn_string):
        storages = [MSSQLScheduleStorage(conn_string) for _ in range(WORKERS)]
        repo_target = _fake_repo_target()
        state = InstigatorState(
            repo_target.get_instigator_origin("test_sensor"),
            InstigatorType.SENSOR,
            InstigatorStatus.RUNNING,
            SensorInstigatorData(min_interval=30),
        )
        clean_schedule_storage.add_instigator_state(state)

        def worker(index: int) -> None:
            for i in range(ITERATIONS):
                storages[index].update_instigator_state(
                    state.with_data(SensorInstigatorData(min_interval=30, cursor=f"{index}-{i}"))
                )

        errors = run_concurrently(worker)
        assert not errors, f"concurrent instigator upserts failed: {errors[:3]!r}"

        states = clean_schedule_storage.all_instigator_state(
            repo_target.get_id(),
            repo_target.get_selector_id(),
            InstigatorType.SENSOR,
        )
        assert len([s for s in states if s.instigator_name == "test_sensor"]) == 1


def _materialization_event(run_id: str, asset_key: str) -> EventLogEntry:
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ASSET_MATERIALIZATION.value,
            "nonce",
            event_specific_data=StepMaterializationData(
                AssetMaterialization(asset_key=AssetKey(asset_key))
            ),
        ),
    )


class TestAssetEvents:
    """`_store_asset_event` upserts `asset_keys`, which every materialization touches.

    This one was expected to be safe -- `asset_keys` grows with the deployment, so the
    optimizer should seek rather than scan and the range locks should stay narrow. It
    deadlocked anyway, on *distinct* asset keys, which is why `store_asset_event` retries
    like the others. Worth keeping as the record of that: the reasoning was sound and the
    measurement disagreed.
    """

    @pytest.fixture
    def event_log(self, conn_string):
        return MSSQLEventLogStorage.create_clean_storage(conn_string)

    def test_distinct_asset_keys(self, event_log, conn_string):
        storages = [MSSQLEventLogStorage(conn_string) for _ in range(WORKERS)]

        def worker(index: int) -> None:
            for i in range(ITERATIONS):
                storages[index].store_event(
                    _materialization_event(make_new_run_id(), f"asset_{index}_{i}")
                )

        errors = run_concurrently(worker)
        assert not errors, f"concurrent asset event writes failed: {errors[:3]!r}"
        assert len(event_log.all_asset_keys()) == WORKERS * ITERATIONS

    def test_same_asset_key(self, event_log, conn_string):
        """The contended case: every worker materialising the same asset."""
        storages = [MSSQLEventLogStorage(conn_string) for _ in range(WORKERS)]

        def worker(index: int) -> None:
            for _ in range(ITERATIONS):
                storages[index].store_event(_materialization_event(make_new_run_id(), "shared"))

        errors = run_concurrently(worker)
        assert not errors, f"concurrent asset event writes failed: {errors[:3]!r}"
        assert [k.to_user_string() for k in event_log.all_asset_keys()] == ["shared"]


class TestReadCommittedSnapshot:
    """RCSI is what makes SQL Server behave like Postgres for dagster's access pattern.

    The README tells operators to enable it; these pin down what it actually buys, so the
    advice does not quietly become wrong.
    """

    def test_a_reader_is_not_blocked_by_an_uncommitted_writer(self, clean_run_storage, conn_string):
        """The daemon writes constantly; the webserver reads constantly.

        Under plain READ COMMITTED the reader waits for the writer's exclusive lock and the
        UI stalls. With RCSI it reads the previous row version and returns immediately.
        """
        clean_run_storage.set_cursor_values({"contended": "before"})

        writer_engine = db.create_engine(conn_string)
        reader_engine = db.create_engine(conn_string)
        try:
            with writer_engine.connect() as writer:
                with writer.begin():  # held open for the duration of the read below
                    writer.execute(
                        db.text("UPDATE kvs SET [value] = 'after' WHERE [key] = 'contended'")
                    )

                    with reader_engine.connect() as reader:
                        # turn a block into a prompt failure rather than a hung test
                        reader.execute(db.text("SET LOCK_TIMEOUT 5000"))
                        value = reader.execute(
                            db.text("SELECT [value] FROM kvs WHERE [key] = 'contended'")
                        ).scalar()

                    # the committed version, not the writer's uncommitted one
                    assert value == "before"
        finally:
            writer_engine.dispose()
            reader_engine.dispose()

    def test_enabled_on_the_test_database(self, conn_string):
        """Guards the tests above: with RCSI off they would pass for the wrong reason."""
        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                enabled = conn.execute(
                    db.text(
                        "SELECT is_read_committed_snapshot_on FROM sys.databases"
                        " WHERE database_id = DB_ID()"
                    )
                ).scalar()
        finally:
            engine.dispose()
        assert enabled, "the test harness is expected to enable READ_COMMITTED_SNAPSHOT"
