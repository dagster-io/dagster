import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from threading import Event
from uuid import uuid4

import pytest
import sqlalchemy as db
from dagster._core.errors import DagsterBackfillAdmissionClosed, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster._core.storage.runs.base import (
    ChildWorkerTarget,
    K8sPodWorkerTarget,
    K8sWorkerTarget,
    UnknownWorkerTarget,
    WorkerLaunchKind,
    WorkerLaunchState,
)
from dagster._core.storage.runs.schema import BackfillWorkerLaunchesTable, RunsTable, RunTagsTable
from dagster._core.storage.sql import run_alembic_downgrade
from dagster._core.storage.tags import (
    AUTO_RETRY_INTENT_TAG,
    BACKFILL_ID_TAG,
    BACKFILL_STOP_PROTOCOL_TAG,
    PARENT_RUN_ID_TAG,
    ROOT_RUN_ID_TAG,
)


@pytest.fixture(params=["sqlite", "postgres"])
def storage_pair(request, tmp_path):
    if request.param == "sqlite":
        storage = SqliteRunStorage.from_local(str(tmp_path))
        other = SqliteRunStorage.from_local(str(tmp_path))
        yield storage, other
        return

    postgres_url = os.getenv("DAGSTER_TEST_POSTGRES_URL")
    if not postgres_url:
        pytest.skip("DAGSTER_TEST_POSTGRES_URL is not set")
    from dagster_postgres.run_storage import PostgresRunStorage

    # Isolate each test's schema so independent suites can share a disposable server.
    schema = f"backfill_stop_{uuid4().hex}"
    engine = db.create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(db.text(f'CREATE SCHEMA "{schema}"'))
    # SQLAlchemy masks credentials in str(URL) on 2.x.
    url = (
        db.engine.make_url(postgres_url)
        .update_query_dict({"options": f"-csearch_path={schema}"})
        .render_as_string(hide_password=False)
    )
    storage = PostgresRunStorage(url)
    other = PostgresRunStorage(url)
    try:
        yield storage, other
    finally:
        storage.dispose()
        other.dispose()
        with engine.connect() as conn:
            conn.execute(db.text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


def add_backfill(storage, status=BulkActionStatus.REQUESTED, protocol=True):
    backfill = PartitionBackfill(
        backfill_id="backfill",
        status=status,
        from_failure=False,
        tags={BACKFILL_STOP_PROTOCOL_TAG: "v2"} if protocol else {},
        backfill_timestamp=1.0,
    )
    storage.add_backfill(backfill)
    return backfill


def add_run(storage, run_id="run", status=DagsterRunStatus.NOT_STARTED, **extra_tags):
    return storage.add_run(
        DagsterRun(
            job_name="job",
            run_id=run_id,
            status=status,
            tags={BACKFILL_ID_TAG: "backfill", **extra_tags},
            root_run_id=extra_tags.get(ROOT_RUN_ID_TAG),
            parent_run_id=extra_tags.get(PARENT_RUN_ID_TAG),
        )
    )


def run_event(storage, run_id, event_type):
    storage.handle_run_event(run_id, DagsterEvent(event_type.value, "job"))


def finish_stop(storage):
    backfill = storage.get_backfill("backfill")
    terminal_status = (
        BulkActionStatus.CANCELED
        if backfill.status == BulkActionStatus.CANCELING
        else BulkActionStatus.FAILED
    )
    storage.update_backfill(backfill.with_status(terminal_status))
    return storage.get_backfill("backfill").status == terminal_status


def claim_run(storage, run_id="run", worker_id="run/run"):
    return storage.claim_backfill_worker_launch(
        run_id, worker_id, WorkerLaunchKind.RUN, UnknownWorkerTarget(handler_name="launcher")
    )


@pytest.mark.parametrize(
    "status", [status for status in BulkActionStatus if status != BulkActionStatus.REQUESTED]
)
def test_closed_backfill_rejects_registration(storage_pair, status):
    storage, _ = storage_pair
    add_backfill(storage, status)
    with pytest.raises(DagsterBackfillAdmissionClosed):
        add_run(storage)
    assert storage.get_runs_count() == 0


def test_protocol_backfill_rejects_empty_owner_identity(storage_pair):
    storage, _ = storage_pair
    backfill = PartitionBackfill(
        backfill_id="",
        status=BulkActionStatus.REQUESTED,
        from_failure=False,
        tags={BACKFILL_STOP_PROTOCOL_TAG: "v2"},
        backfill_timestamp=1.0,
    )
    with pytest.raises(DagsterInvariantViolationError, match="nonempty owner ID"):
        storage.add_backfill(backfill)
    assert storage.get_backfill("") is None


def test_historical_import_only_bypasses_gate_for_terminal_runs(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage, BulkActionStatus.CANCELED)
    run = DagsterRun(job_name="job", run_id="run", tags={BACKFILL_ID_TAG: "backfill"})
    from dagster._time import get_current_datetime

    with pytest.raises(DagsterBackfillAdmissionClosed):
        storage.add_historical_run(run, get_current_datetime())
    storage.add_historical_run(run.with_status(DagsterRunStatus.SUCCESS), get_current_datetime())
    assert storage.get_runs()[0].tags[BACKFILL_ID_TAG] == "backfill"


def test_launch_claim_persists_and_requires_acknowledgment_and_terminal_run(storage_pair):
    storage, restarted = storage_pair
    add_backfill(storage)
    add_run(storage)
    assert claim_run(storage)
    assert not claim_run(restarted)
    assert not claim_run(restarted, worker_id="another-run-worker")
    pending = restarted.get_backfill_worker_launches("backfill")
    assert len(pending) == 1
    assert pending[0].state == WorkerLaunchState.PENDING
    storage.resolve_backfill_worker_launch("run", "run/run")
    assert restarted.get_backfill_worker_launches("backfill") == pending
    storage.acknowledge_backfill_worker_launch("run", "run/run")
    storage.resolve_backfill_worker_launch("run", "run/run")
    assert restarted.get_backfill_worker_launches("backfill")[0].acknowledged
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    storage.resolve_backfill_worker_launch("run", "run/run")
    assert restarted.get_backfill_worker_launches("backfill") == []
    assert not claim_run(restarted)


def test_unacknowledged_dispatch_blocks_completion_after_terminal_status(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage)
    assert claim_run(storage)
    storage.request_backfill_stop("backfill")
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    storage.resolve_backfill_worker_launch("run", "run/run")
    assert not finish_stop(storage)
    assert storage.get_backfill("backfill").status == BulkActionStatus.CANCELING


def test_step_attempts_are_independent_and_can_resolve_while_run_is_started(storage_pair):
    storage, restarted = storage_pair
    add_backfill(storage)
    add_run(storage, status=DagsterRunStatus.STARTED)
    target = K8sWorkerTarget(job_name="step-job", namespace="namespace")
    assert storage.claim_backfill_worker_launch("run", "step/one/0", WorkerLaunchKind.STEP, target)
    assert not restarted.claim_backfill_worker_launch(
        "run",
        "step/one/0",
        WorkerLaunchKind.STEP,
        K8sWorkerTarget(job_name="changed-job", namespace="changed-namespace"),
    )
    assert restarted.get_backfill_worker_launches("backfill")[0].target == target
    storage.acknowledge_backfill_worker_launch("run", "step/one/0")
    storage.resolve_backfill_worker_launch("run", "step/one/0")
    assert restarted.get_backfill_worker_launches("backfill") == []
    assert not storage.claim_backfill_worker_launch(
        "run", "step/one/0", WorkerLaunchKind.STEP, target
    )
    assert storage.claim_backfill_worker_launch("run", "step/one/1", WorkerLaunchKind.STEP, target)
    storage.request_backfill_stop("backfill")
    assert not storage.claim_backfill_worker_launch(
        "run", "step/two/0", WorkerLaunchKind.STEP, target
    )
    storage.acknowledge_backfill_worker_launch("run", "step/one/1")
    storage.resolve_backfill_worker_launch("run", "step/one/1")
    assert not finish_stop(storage)
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    assert finish_stop(storage)


@pytest.mark.parametrize(
    "closed_status",
    [
        BulkActionStatus.CANCELING,
        BulkActionStatus.FAILING,
        BulkActionStatus.CANCELED,
        BulkActionStatus.FAILED,
    ],
)
def test_stale_progress_cannot_reopen_closed_backfill(storage_pair, closed_status):
    storage, _ = storage_pair
    old = add_backfill(storage)
    storage.update_backfill(old.with_status(closed_status))
    storage.update_backfill(old.with_partition_checkpoint("old-progress"))
    current = storage.get_backfill("backfill")
    assert current.status == closed_status
    assert current.last_submitted_partition_name is None
    if closed_status == BulkActionStatus.FAILED:
        assert storage.resume_backfill("backfill").status == BulkActionStatus.REQUESTED
    else:
        with pytest.raises(DagsterInvariantViolationError):
            storage.resume_backfill("backfill")


@pytest.mark.parametrize(
    "stop_status,terminal_status",
    [
        (BulkActionStatus.CANCELING, BulkActionStatus.CANCELED),
        (BulkActionStatus.FAILING, BulkActionStatus.FAILED),
    ],
)
def test_every_unfinished_owned_run_and_ledger_entry_must_drain(
    storage_pair, stop_status, terminal_status
):
    storage, _ = storage_pair
    backfill = add_backfill(storage)
    add_run(storage)
    assert claim_run(storage)
    storage.acknowledge_backfill_worker_launch("run", "run/run")
    storage.update_backfill(backfill.with_status(stop_status))
    assert not finish_stop(storage)
    storage.update_backfill(backfill.with_status(terminal_status))
    assert storage.get_backfill("backfill").status == stop_status
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    assert not finish_stop(storage)
    storage.resolve_backfill_worker_launch("run", "run/run")
    assert finish_stop(storage)
    assert storage.get_backfill("backfill").status == terminal_status


def test_direct_failure_enters_drain_before_terminal_failure(storage_pair):
    storage, _ = storage_pair
    backfill = add_backfill(storage)
    add_run(storage)
    storage.update_backfill(backfill.with_status(BulkActionStatus.FAILED))
    assert storage.get_backfill("backfill").status == BulkActionStatus.FAILING
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    assert finish_stop(storage)


@pytest.mark.parametrize(
    "event_type",
    [
        DagsterEventType.PIPELINE_ENQUEUED,
        DagsterEventType.PIPELINE_STARTING,
        DagsterEventType.PIPELINE_START,
    ],
)
def test_late_events_cannot_resurrect_run_after_closed_backfill_drain(storage_pair, event_type):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage)
    storage.request_backfill_stop("backfill")
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    assert finish_stop(storage)
    run_event(storage, "run", event_type)
    assert storage.get_runs()[0].status == DagsterRunStatus.CANCELED


def test_backfill_owner_survives_tag_mutation_in_reads_filters_and_run_groups(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage, run_id="root")
    add_run(storage, **{ROOT_RUN_ID_TAG: "root", PARENT_RUN_ID_TAG: "root"})
    with pytest.raises(DagsterInvariantViolationError, match="ownership is immutable"):
        storage.add_run_tags("run", {BACKFILL_ID_TAG: "different", "mutable": "yes"})
    storage.add_run_tags("run", {"mutable": "yes"})
    assert storage.get_run_tags([BACKFILL_ID_TAG]) == [(BACKFILL_ID_TAG, {"backfill"})]
    assert (
        storage.get_runs(filters=RunsFilter(run_ids=["run"]))[0].tags[BACKFILL_ID_TAG] == "backfill"
    )
    assert len(storage.get_runs(filters=RunsFilter(tags={BACKFILL_ID_TAG: "backfill"}))) == 2
    assert storage.get_runs(filters=RunsFilter(tags={BACKFILL_ID_TAG: "different"})) == []
    assert storage.get_run_group("run")[1][1].tags[BACKFILL_ID_TAG] == "backfill"
    storage.request_backfill_stop("backfill")
    assert not claim_run(storage)
    assert not finish_stop(storage)


@pytest.mark.parametrize("operation", ["register", "run_claim", "step_claim"])
def test_closure_waits_for_admission_transaction(storage_pair, monkeypatch, operation):
    storage, other = storage_pair
    add_backfill(storage)
    if operation != "register":
        add_run(
            storage,
            status=DagsterRunStatus.STARTED
            if operation == "step_claim"
            else DagsterRunStatus.NOT_STARTED,
        )
    locked, release = Event(), Event()
    original_lock = storage._find_locked_backfill  # noqa: SLF001

    def pause_after_lock(conn, backfill_id):
        backfill = original_lock(conn, backfill_id)
        locked.set()
        assert release.wait(5)
        return backfill

    monkeypatch.setattr(storage, "_find_locked_backfill", pause_after_lock)

    def admit():
        if operation == "register":
            return add_run(storage)
        if operation == "run_claim":
            return claim_run(storage)
        return storage.claim_backfill_worker_launch(
            "run",
            "step/one/0",
            WorkerLaunchKind.STEP,
            K8sWorkerTarget(job_name="step", namespace="ns"),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        admission = pool.submit(admit)
        assert locked.wait(5)
        closure = pool.submit(other.request_backfill_stop, "backfill")
        try:
            with pytest.raises(TimeoutError):
                closure.result(timeout=0.1)
        finally:
            release.set()
        assert admission.result(timeout=5)
        assert closure.result(timeout=5).status == BulkActionStatus.CANCELING
    assert not finish_stop(other)


def test_registration_and_tag_insert_rollback_together(storage_pair, monkeypatch):
    storage, _ = storage_pair
    add_backfill(storage)
    original_transaction = storage._backfill_transaction  # noqa: SLF001

    @contextmanager
    def fail_tag_insert():
        with original_transaction() as conn:
            original_execute = conn.execute

            def execute(statement, *args, **kwargs):
                if getattr(statement, "table", None) is RunTagsTable and statement.is_insert:
                    raise RuntimeError("tag insert failed")
                return original_execute(statement, *args, **kwargs)

            monkeypatch.setattr(conn, "execute", execute)
            yield conn

    monkeypatch.setattr(storage, "_backfill_transaction", fail_tag_insert)
    with pytest.raises(RuntimeError, match="tag insert failed"):
        add_run(storage)
    assert storage.get_runs_count() == 0


def test_missing_ledger_migration_fails_closed(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    with storage.connect() as conn:
        BackfillWorkerLaunchesTable.drop(conn)
        conn.execute(
            db.text("UPDATE alembic_version SET version_num = :version"),
            {"version": "29b539ebc72a"},
        )
    assert not storage.supports_backfill_stop_protocol
    with pytest.raises(DagsterInvariantViolationError, match="storage migration"):
        add_run(storage)
    with pytest.raises(DagsterInvariantViolationError, match="storage migration"):
        storage.request_backfill_stop("backfill")
    storage.upgrade()
    assert storage.supports_backfill_stop_protocol
    assert add_run(storage)


def test_in_memory_storage_supports_atomic_admission():
    storage = InMemoryRunStorage()
    try:
        assert storage.supports_backfill_stop_protocol
        add_backfill(storage)
        storage.request_backfill_stop("backfill")
        with pytest.raises(DagsterBackfillAdmissionClosed):
            add_run(storage)
    finally:
        storage.dispose()


def test_unmarked_backfills_keep_released_registration_and_resume_behavior(storage_pair):
    storage, _ = storage_pair
    backfill = add_backfill(storage, BulkActionStatus.CANCELED, protocol=False)
    assert add_run(storage)
    assert claim_run(storage)
    assert storage.get_backfill_worker_launches("backfill") == []
    assert storage.resume_backfill("backfill").status == BulkActionStatus.REQUESTED
    storage.update_backfill(backfill.with_status(BulkActionStatus.CANCELING))
    storage.update_backfill(backfill.with_status(BulkActionStatus.CANCELED))
    assert storage.get_backfill("backfill").status == BulkActionStatus.CANCELED


def test_protocol_marker_cannot_be_removed_or_added_by_progress_updates(storage_pair):
    storage, _ = storage_pair
    backfill = add_backfill(storage)
    storage.update_backfill(backfill._replace(tags={}))
    assert storage.get_backfill("backfill").tags[BACKFILL_STOP_PROTOCOL_TAG] == "v2"
    storage.request_backfill_stop("backfill")
    with pytest.raises(DagsterBackfillAdmissionClosed):
        add_run(storage)
    unmarked = PartitionBackfill(
        "unmarked",
        status=BulkActionStatus.REQUESTED,
        from_failure=False,
        tags={},
        backfill_timestamp=1.0,
    )
    storage.add_backfill(unmarked)
    storage.update_backfill(unmarked._replace(tags={BACKFILL_STOP_PROTOCOL_TAG: "v2"}))
    assert BACKFILL_STOP_PROTOCOL_TAG not in storage.get_backfill("unmarked").tags


def test_unresolved_dispatch_prevents_run_deletion(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage)
    assert claim_run(storage)
    with pytest.raises(DagsterInvariantViolationError, match="unresolved"):
        storage.delete_run("run")
    storage.acknowledge_backfill_worker_launch("run", "run/run")
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    storage.resolve_backfill_worker_launch("run", "run/run")
    storage.delete_run("run")
    assert storage.get_runs_count() == 0


def test_aggregate_completion_requires_worker_resolution(storage_pair):
    storage, _ = storage_pair
    backfill = add_backfill(storage)
    add_run(storage)
    assert claim_run(storage)
    storage.acknowledge_backfill_worker_launch("run", "run/run")
    run_event(storage, "run", DagsterEventType.PIPELINE_SUCCESS)
    storage.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED_SUCCESS))
    assert storage.get_backfill("backfill").status == BulkActionStatus.REQUESTED
    storage.resolve_backfill_worker_launch("run", "run/run")
    storage.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED_SUCCESS))
    assert storage.get_backfill("backfill").status == BulkActionStatus.COMPLETED_SUCCESS


def retry_child(run_id, automatic=True, intent="auto-retry:parent"):
    return DagsterRun(
        job_name="job",
        run_id=run_id,
        parent_run_id="parent",
        root_run_id="parent",
        tags={
            BACKFILL_ID_TAG: "backfill",
            **({AUTO_RETRY_INTENT_TAG: intent} if automatic else {}),
        },
    )


def test_simultaneous_automatic_retry_registration_reuses_one_child(storage_pair):
    storage, other = storage_pair
    add_backfill(storage)
    add_run(storage, run_id="parent", status=DagsterRunStatus.FAILURE)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(storage.add_run, retry_child("first"))
        second = pool.submit(other.add_run, retry_child("second"))
        first_run = first.result(timeout=5)
        second_run = second.result(timeout=5)
    assert first_run.run_id == second_run.run_id
    assert storage.get_runs_count() == 2
    storage.request_backfill_stop("backfill")
    assert other.add_run(retry_child("third")).run_id == first_run.run_id
    assert storage.get_runs_count() == 2


def test_manual_reexecution_children_do_not_share_automatic_retry_intent(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage, run_id="parent", status=DagsterRunStatus.FAILURE)
    assert storage.add_run(retry_child("first", automatic=False)).run_id == "first"
    assert storage.add_run(retry_child("second", automatic=False)).run_id == "second"
    assert storage.get_runs_count() == 3


def test_retry_intent_must_identify_the_actual_failed_parent(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage, run_id="parent", status=DagsterRunStatus.FAILURE)
    with pytest.raises(DagsterInvariantViolationError, match="failed parent"):
        storage.add_run(retry_child("child", intent="auto-retry:different-parent"))


def test_active_historical_import_rejected_even_before_closure(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    from dagster._time import get_current_datetime

    with pytest.raises(DagsterBackfillAdmissionClosed, match="Historical active workers"):
        storage.add_historical_run(
            DagsterRun(job_name="job", run_id="run", tags={BACKFILL_ID_TAG: "backfill"}),
            get_current_datetime(),
        )


def test_run_claim_rejects_already_started_worker(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage, status=DagsterRunStatus.STARTED)
    assert not claim_run(storage)
    assert storage.get_backfill_worker_launches("backfill") == []


def test_postgres_commands_work_with_one_connection_pool(storage_pair):
    storage, _ = storage_pair
    if isinstance(storage, SqliteRunStorage):
        pytest.skip("Postgres connection pool regression")
    storage._engine.dispose()  # noqa: SLF001
    storage._engine = db.create_engine(  # noqa: SLF001
        storage.postgres_url,
        isolation_level="AUTOCOMMIT",
        pool_size=1,
        max_overflow=0,
        pool_timeout=0.2,
    )
    add_backfill(storage)
    add_run(storage)
    assert claim_run(storage)
    storage.acknowledge_backfill_worker_launch("run", "run/run")
    storage.request_backfill_stop("backfill")
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    storage.resolve_backfill_worker_launch("run", "run/run")
    assert finish_stop(storage)
    storage.delete_run("run")


def test_actual_prior_schema_upgrades_retry_intent_and_worker_ledger(storage_pair):
    storage, _ = storage_pair
    if isinstance(storage, SqliteRunStorage):
        storage._alembic_downgrade(rev="29b539ebc72a")  # noqa: SLF001
    else:
        from dagster_postgres.run_storage import run_storage as pg_run_storage
        from dagster_postgres.utils import pg_alembic_config

        with storage.connect() as conn:
            run_alembic_downgrade(
                pg_alembic_config(pg_run_storage.__file__), conn, rev="29b539ebc72a"
            )
    with storage.connect() as conn:
        inspector = db.inspect(conn)
        assert "auto_retry_intent" not in {
            column["name"] for column in inspector.get_columns("runs")
        }
        assert not inspector.has_table(BackfillWorkerLaunchesTable.name)
    assert not storage.supports_backfill_stop_protocol
    storage.upgrade()
    assert storage.supports_backfill_stop_protocol
    add_backfill(storage)
    add_run(storage, run_id="parent", status=DagsterRunStatus.FAILURE)
    child = storage.add_run(retry_child("first"))
    assert storage.add_run(retry_child("second")).run_id == child.run_id
    assert claim_run(storage, run_id=child.run_id)


@pytest.mark.parametrize("owner", ["missing", ""])
def test_registration_rejects_missing_backfill_owner(storage_pair, owner):
    storage, _ = storage_pair
    with pytest.raises(DagsterBackfillAdmissionClosed, match="not present"):
        storage.add_run(
            DagsterRun(
                job_name="job",
                run_id="orphan",
                tags={BACKFILL_ID_TAG: owner, BACKFILL_STOP_PROTOCOL_TAG: "v2"},
            )
        )
    assert storage.get_runs_count() == 0


@pytest.mark.parametrize("operation", ["claim", "acknowledge", "resolve"])
def test_persisted_orphan_never_escapes_worker_protocol(storage_pair, operation):
    storage, _ = storage_pair
    from dagster._time import get_current_datetime

    # Historical terminal import is the named archive boundary. A nonterminal SQL
    # row models an orphan persisted by a released version before this protocol.
    storage.add_historical_run(
        DagsterRun(
            job_name="job",
            run_id="run",
            status=DagsterRunStatus.SUCCESS,
            tags={BACKFILL_ID_TAG: "missing"},
        ),
        get_current_datetime(),
    )
    with storage.connect() as conn:
        conn.execute(
            RunsTable.update()
            .where(RunsTable.c.run_id == "run")
            .values(status=DagsterRunStatus.STARTING.value)
        )
    with pytest.raises(DagsterBackfillAdmissionClosed, match="not present"):
        if operation == "claim":
            claim_run(storage)
        elif operation == "acknowledge":
            storage.acknowledge_backfill_worker_launch("run", "run/run")
        else:
            storage.resolve_backfill_worker_launch("run", "run/run")


def test_disabled_legacy_registration_retains_synthetic_backfill_tags(storage_pair):
    storage, _ = storage_pair
    run = storage.add_run(
        DagsterRun(job_name="job", run_id="legacy", tags={BACKFILL_ID_TAG: "missing"})
    )
    assert run.tags[BACKFILL_ID_TAG] == "missing"
    with pytest.raises(DagsterBackfillAdmissionClosed, match="not present"):
        claim_run(storage, run_id=run.run_id)


@pytest.mark.parametrize(
    "status",
    [
        BulkActionStatus.REQUESTED,
        BulkActionStatus.CANCELING,
        BulkActionStatus.FAILING,
        BulkActionStatus.FAILED,
    ],
)
def test_auto_retry_intent_survives_attempted_child_deletion_and_replay(storage_pair, status):
    storage, _ = storage_pair
    backfill = add_backfill(storage)
    add_run(storage, run_id="parent", status=DagsterRunStatus.FAILURE)
    child = storage.add_run(retry_child("child"))
    run_event(storage, child.run_id, DagsterEventType.PIPELINE_FAILURE)
    storage.update_backfill(backfill.with_status(status))
    with pytest.raises(DagsterInvariantViolationError, match="automatic retry"):
        storage.delete_run(child.run_id)
    if status == BulkActionStatus.FAILED:
        storage.resume_backfill("backfill")
    assert storage.add_run(retry_child("replayed-child")).run_id == child.run_id
    assert storage.get_runs_count() == 2


def test_automatic_child_can_be_deleted_after_permanent_backfill_closure(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage, run_id="parent", status=DagsterRunStatus.FAILURE)
    child = storage.add_run(retry_child("child"))
    run_event(storage, child.run_id, DagsterEventType.PIPELINE_CANCELED)
    storage.request_backfill_stop("backfill")
    assert finish_stop(storage)
    storage.delete_run(child.run_id)
    with pytest.raises(DagsterBackfillAdmissionClosed):
        storage.add_run(retry_child("replayed-child"))


def test_registered_owned_run_retains_immutable_protocol_version(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    registered = add_run(storage)
    assert registered.tags[BACKFILL_STOP_PROTOCOL_TAG] == "v2"
    assert storage.get_runs()[0].tags[BACKFILL_STOP_PROTOCOL_TAG] == "v2"
    assert storage.get_run_tags([BACKFILL_STOP_PROTOCOL_TAG]) == [
        (BACKFILL_STOP_PROTOCOL_TAG, {"v2"})
    ]
    with pytest.raises(DagsterInvariantViolationError, match="version is immutable"):
        storage.add_run_tags(registered.run_id, {BACKFILL_STOP_PROTOCOL_TAG: ""})
    with pytest.raises(DagsterInvariantViolationError, match="version is immutable"):
        storage.add_run_tags(registered.run_id, {BACKFILL_STOP_PROTOCOL_TAG: "v3"})
    # The durable run marker survives removal of the owner, independent of any
    # current instance enablement setting.
    from dagster._core.storage.runs.schema import BulkActionsTable

    with storage.connect() as conn:
        conn.execute(BulkActionsTable.delete().where(BulkActionsTable.c.key == "backfill"))
    assert storage.get_runs()[0].tags[BACKFILL_STOP_PROTOCOL_TAG] == "v2"
    with pytest.raises(DagsterBackfillAdmissionClosed, match="not present"):
        claim_run(storage)


def child_target(parent="job", admission="admission"):
    return ChildWorkerTarget(
        parent_worker_id=parent,
        resource=K8sPodWorkerTarget(
            pod_name=f"pod-{admission}",
            namespace="workers",
            admission_id=admission,
            job_name="step-job",
            job_uid="job-uid",
        ),
    )


def prepare_child_parent(storage):
    add_backfill(storage)
    add_run(storage, status=DagsterRunStatus.STARTED)
    assert storage.claim_backfill_worker_launch(
        "run",
        "job",
        WorkerLaunchKind.STEP,
        K8sWorkerTarget(job_name="step-job", namespace="workers"),
    )
    storage.acknowledge_backfill_worker_launch("run", "job")


def test_child_receipt_survives_closure_and_blocks_finalization_before_persistence(storage_pair):
    storage, restarted = storage_pair
    prepare_child_parent(storage)
    target = child_target()
    assert storage.admit_backfill_worker_child("run", "pod", target)
    storage.request_backfill_stop("backfill")
    storage.resolve_backfill_worker_launch("run", "job")
    run_event(storage, "run", DagsterEventType.PIPELINE_CANCELED)
    assert restarted.admit_backfill_worker_child("run", "pod", target)
    assert not restarted.admit_backfill_worker_child(
        "run", "late-pod", child_target(admission="late")
    )
    assert not finish_stop(storage)
    storage.resolve_backfill_worker_launch("run", "pod")
    assert not finish_stop(storage)
    restarted.acknowledge_backfill_worker_launch("run", "pod")
    assert not restarted.admit_backfill_worker_child("run", "pod", target)
    restarted.resolve_backfill_worker_launch("run", "pod")
    assert finish_stop(storage)
    assert not restarted.admit_backfill_worker_child("run", "pod", target)


def test_resolved_parent_rejects_new_child_while_backfill_remains_open(storage_pair):
    storage, _ = storage_pair
    prepare_child_parent(storage)
    storage.resolve_backfill_worker_launch("run", "job")
    assert not storage.admit_backfill_worker_child("run", "pod", child_target())
    assert storage.get_backfill_worker_launches("backfill") == []


def test_child_replay_cannot_change_parent_or_resource(storage_pair):
    storage, _ = storage_pair
    prepare_child_parent(storage)
    target = child_target()
    assert storage.admit_backfill_worker_child("run", "pod", target)
    assert not storage.admit_backfill_worker_child("run", "pod", child_target(parent="other"))
    assert not storage.admit_backfill_worker_child("run", "pod", child_target(admission="other"))
    children = [
        claim
        for claim in storage.get_backfill_worker_launches("backfill")
        if claim.kind == WorkerLaunchKind.CHILD
    ]
    assert len(children) == 1 and children[0].target == target


def test_missing_parent_rejects_child_without_a_claim(storage_pair):
    storage, _ = storage_pair
    add_backfill(storage)
    add_run(storage)
    assert not storage.admit_backfill_worker_child("run", "pod", child_target())
    assert storage.get_backfill_worker_launches("backfill") == []


def test_child_schema_upgrade_retains_existing_logical_dispatches(storage_pair):
    storage, _ = storage_pair
    prepare_child_parent(storage)
    if isinstance(storage, SqliteRunStorage):
        storage._alembic_downgrade(rev="4e7a9c31b602")  # noqa: SLF001
    else:
        from dagster_postgres.run_storage import run_storage as pg_run_storage
        from dagster_postgres.utils import pg_alembic_config

        with storage.connect() as conn:
            run_alembic_downgrade(
                pg_alembic_config(pg_run_storage.__file__), conn, rev="4e7a9c31b602"
            )
    assert not storage.supports_backfill_stop_protocol
    with pytest.raises(DagsterInvariantViolationError, match="storage migration"):
        storage.admit_backfill_worker_child("run", "pod", child_target())
    storage.upgrade()
    assert storage.supports_backfill_stop_protocol
    assert storage.get_backfill_worker_launches("backfill")[0].worker_id == "job"
    assert storage.admit_backfill_worker_child("run", "pod", child_target())


@pytest.mark.parametrize("winner", ["child", "resolve"])
def test_parent_resolution_and_child_admission_serialize(storage_pair, monkeypatch, winner):
    storage, other = storage_pair
    prepare_child_parent(storage)
    locked, release, competing = Event(), Event(), Event()
    original = storage._lock_backfill  # noqa: SLF001

    def hold_gate(conn, owner):
        value = original(conn, owner)
        locked.set()
        assert release.wait(5)
        return value

    monkeypatch.setattr(storage, "_lock_backfill", hold_gate)

    def admit(store):
        return store.admit_backfill_worker_child("run", "pod", child_target())

    def resolve(store):
        store.resolve_backfill_worker_launch("run", "job")

    first, second = (admit, resolve) if winner == "child" else (resolve, admit)

    def contend():
        competing.set()
        return second(other)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_result = executor.submit(first, storage)
        assert locked.wait(5)
        second_result = executor.submit(contend)
        try:
            assert competing.wait(5)
            with pytest.raises(TimeoutError):
                second_result.result(timeout=0.05)
        finally:
            release.set()
        first_value = first_result.result(timeout=5)
        second_value = second_result.result(timeout=5)
    admitted = first_value if winner == "child" else second_value
    assert admitted is (winner == "child")
    children = [
        claim
        for claim in storage.get_backfill_worker_launches("backfill")
        if claim.kind == WorkerLaunchKind.CHILD
    ]
    assert len(children) == int(winner == "child")
