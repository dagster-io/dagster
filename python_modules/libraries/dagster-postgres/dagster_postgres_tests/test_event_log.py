import gc
import time
from contextlib import contextmanager

import objgraph
import pytest
from dagster import AssetKey, AssetMaterialization, EventLogEntry
from dagster._core.events import (
    AssetWipedData,
    DagsterEvent,
    DagsterEventType,
    StepMaterializationData,
)
from dagster._core.instance import RUNLESS_JOB_NAME, RUNLESS_RUN_ID
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.event_log.migration import ASSET_KEY_INDEX_COLS
from dagster._core.storage.event_log.schema import SecondaryIndexMigrationTable
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster._core.utils import make_new_run_id
from dagster_postgres.event_log import PostgresEventLogStorage
from dagster_shared.yaml_utils import safe_load_yaml

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.event_log_storage import (
    TestEventLogStorage,
    create_test_event_log_record,
)


@contextmanager
def _clean_storage(conn_string):
    storage = PostgresEventLogStorage.create_clean_storage(conn_string)
    assert storage
    try:
        yield storage
    finally:
        storage.dispose()


class TestPostgresEventLogStorage(TestEventLogStorage):
    __test__ = True

    @pytest.fixture(name="instance", scope="function")
    def instance(self, conn_string):
        PostgresEventLogStorage.create_clean_storage(conn_string)

        with instance_for_test(
            overrides={"storage": {"postgres": {"postgres_url": conn_string}}}
        ) as instance:
            yield instance

    @pytest.fixture(scope="function", name="storage")
    def event_log_storage(self, instance):
        event_log_storage = instance.event_log_storage
        assert isinstance(event_log_storage, PostgresEventLogStorage)
        yield event_log_storage

    def can_wipe_asset_partitions(self) -> bool:
        return False

    def test_store_planned_events_batch_on_conflict_updates_asset_keys(self, conn_string):
        """Postgres-specific: re-running a batch of ASSET_MATERIALIZATION_PLANNED events for
        an asset key that already has a row in AssetKeyTable should *update* the existing row
        via ON CONFLICT DO UPDATE rather than fail or insert a duplicate. This exercises the
        upsert path that the shared sqlite/in-memory inherited tests do not cover (those
        storages fall through to the base per-event loop).
        """
        import dagster as dg
        from dagster._core.events import (
            AssetMaterializationPlannedData,
            DagsterEvent,
            DagsterEventType,
        )
        from dagster._core.events.log import EventLogEntry
        from dagster._core.storage.event_log.schema import AssetKeyTable

        with _clean_storage(conn_string) as storage:
            asset_key = dg.AssetKey(["pg_planned_conflict"])
            first_run_id = make_new_run_id()
            second_run_id = make_new_run_id()

            def _planned_event(run_id):
                return EventLogEntry(
                    error_info=None,
                    level="debug",
                    user_message="",
                    run_id=run_id,
                    timestamp=time.time(),
                    dagster_event=DagsterEvent(
                        DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                        "nonce",
                        event_specific_data=AssetMaterializationPlannedData(asset_key),
                    ),
                )

            storage.store_event_batch([_planned_event(first_run_id)])

            records = storage.get_asset_records([asset_key])
            assert len(records) == 1
            assert records[0].asset_entry.last_run_id == first_run_id

            # Second batch for the same key must UPDATE (not raise IntegrityError, not duplicate)
            storage.store_event_batch([_planned_event(second_run_id)])

            with storage.index_connection() as conn:
                row_count = conn.execute(
                    AssetKeyTable.select().where(AssetKeyTable.c.asset_key == asset_key.to_string())
                ).rowcount
            assert row_count == 1

            records = storage.get_asset_records([asset_key])
            assert len(records) == 1
            assert records[0].asset_entry.last_run_id == second_run_id

    def test_store_planned_events_batch_chunks_check_execution_rows(self, conn_string, monkeypatch):
        """Postgres-specific: the asset_check_executions bulk INSERT fans out to one row
        per (event x partition), so the row count can exceed PG's 65_535 bind-parameter
        ceiling even when the *event* count is under DAGSTER_PLANNED_EVENT_CHUNK_SIZE.
        Verify the storage layer chunks by row count and still produces the full set.
        """
        import dagster as dg
        import dagster_postgres.event_log.event_log as pg_event_log
        from dagster._core.definitions.asset_checks.asset_check_evaluation import (
            AssetCheckEvaluationPlanned,
        )
        from dagster._core.definitions.partitions.definition import StaticPartitionsDefinition
        from dagster._core.events import DagsterEvent, DagsterEventType
        from dagster._core.events.log import EventLogEntry

        # Squeeze the row cap so we don't have to allocate 8k partitions in a test.
        monkeypatch.setattr(pg_event_log, "_CHECK_EXECUTION_ROWS_PER_INSERT", 3)

        partition_keys = ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]
        partitions_def = StaticPartitionsDefinition(partition_keys)
        partitions_subset = partitions_def.subset_with_partition_keys(partition_keys)

        with _clean_storage(conn_string) as storage:
            run_id = make_new_run_id()
            check_key = dg.AssetCheckKey(dg.AssetKey(["pg_chunk_check"]), "c")
            event = EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetCheckEvaluationPlanned(
                        asset_key=check_key.asset_key,
                        check_name=check_key.name,
                        partitions_subset=partitions_subset,
                    ),
                ),
            )

            storage.store_event_batch([event])

            history = storage.get_asset_check_execution_history(check_key, limit=20)
            assert len(history) == 7
            assert {r.partition for r in history} == set(partition_keys)

    def test_store_planned_events_batch_rolls_back_on_partial_failure(self, conn_string):
        """Postgres-specific: if the asset-check-execution insert fails mid-batch, the
        wrapping transaction must roll back so that no event-log rows are committed.
        The outer `_store_and_notify` fallback then re-runs per-event without producing
        duplicate rows.
        """
        from dagster._core.events import DagsterEvent, DagsterEventType
        from dagster._core.events.log import EventLogEntry

        with _clean_storage(conn_string) as storage:
            run_id = make_new_run_id()

            # Build a planned check event with malformed event_specific_data (None)
            # so the bulk check-execution insert raises mid-transaction. The event-log
            # bulk insert should not be visible after the rollback.
            bad_event = EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                    "nonce",
                    event_specific_data=None,  # forces the check insert helper to raise
                ),
            )

            with pytest.raises(Exception):
                storage.store_event_batch([bad_event])

            records = storage.get_records_for_run(
                run_id, of_type=DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
            ).records
            assert records == []

    def test_event_log_storage_two_watchers(self, conn_string):
        with _clean_storage(conn_string) as storage:
            run_id = make_new_run_id()
            watched_1 = []
            watched_2 = []

            def watch_one(event, _cursor):
                watched_1.append(event)

            def watch_two(event, _cursor):
                watched_2.append(event)

            assert len(storage.get_logs_for_run(run_id)) == 0

            storage.store_event(create_test_event_log_record(str(1), run_id=run_id))
            assert len(storage.get_logs_for_run(run_id)) == 1
            assert len(watched_1) == 0

            storage.watch(run_id, str(EventLogCursor.from_storage_id(1)), watch_one)

            storage.store_event(create_test_event_log_record(str(2), run_id=run_id))
            storage.store_event(create_test_event_log_record(str(3), run_id=run_id))

            storage.watch(run_id, str(EventLogCursor.from_storage_id(3)), watch_two)
            storage.store_event(create_test_event_log_record(str(4), run_id=run_id))

            attempts = 10
            while (len(watched_1) < 3 or len(watched_2) < 1) and attempts > 0:
                time.sleep(0.5)
                attempts -= 1
            assert len(watched_1) == 3
            assert len(watched_2) == 1

            assert len(storage.get_logs_for_run(run_id)) == 4

            storage.end_watch(run_id, watch_one)
            time.sleep(0.3)  # this value scientifically selected from a range of attractive values
            storage.store_event(create_test_event_log_record(str(5), run_id=run_id))

            attempts = 10
            while len(watched_2) < 2 and attempts > 0:
                time.sleep(0.5)
                attempts -= 1
            assert len(watched_1) == 3
            assert len(watched_2) == 2

            storage.end_watch(run_id, watch_two)

            assert len(storage.get_logs_for_run(run_id)) == 5

            storage.delete_events(run_id)

            assert len(storage.get_logs_for_run(run_id)) == 0
            assert len(watched_1) == 3
            assert len(watched_2) == 2

            assert [int(evt.message) for evt in watched_1] == [2, 3, 4]
            assert [int(evt.message) for evt in watched_2] == [4, 5]
            assert len(objgraph.by_type("SqlPollingEventWatcher")) == 1

        # ensure we clean up poller on exit
        gc.collect()
        assert len(objgraph.by_type("SqlPollingEventWatcher")) == 0

    def test_load_from_config(self, hostname):
        url_cfg = f"""
        event_log_storage:
            module: dagster_postgres.event_log
            class: PostgresEventLogStorage
            config:
                postgres_url: postgresql://test:test@{hostname}:5432/test
        """

        explicit_cfg = f"""
        event_log_storage:
            module: dagster_postgres.event_log
            class: PostgresEventLogStorage
            config:
                postgres_db:
                    username: test
                    password: test
                    hostname: {hostname}
                    db_name: test
        """

        with instance_for_test(overrides=safe_load_yaml(url_cfg)) as from_url_instance:
            from_url = from_url_instance._event_storage  # noqa: SLF001

            with instance_for_test(overrides=safe_load_yaml(explicit_cfg)) as explicit_instance:
                from_explicit = explicit_instance._event_storage  # noqa: SLF001

                assert from_url.postgres_url == from_explicit.postgres_url  # ty: ignore[unresolved-attribute]


def test_all_asset_keys_excludes_wiped_asset_on_legacy_index_path(conn_string):
    # Regression test for the legacy (pre-ASSET_KEY_INDEX_COLS-migration) read path, where wiped
    # assets are filtered by comparing the wipe timestamp against the latest event log timestamp.
    # The ASSET_WIPED event stored immediately after a wipe (and any other event type that does
    # not update last_materialization_timestamp on the migrated path) must not make the wiped
    # asset appear live.
    asset_key = AssetKey(["asset_one"])
    with _clean_storage(conn_string) as storage:
        # simulate a storage that has not run the ASSET_KEY_INDEX_COLS data migration
        with storage.index_connection() as conn:
            conn.execute(SecondaryIndexMigrationTable.delete())
        storage._secondary_index_cache.clear()  # noqa: SLF001
        assert not storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=make_new_run_id(),
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION.value,
                    "nonce",
                    event_specific_data=StepMaterializationData(
                        AssetMaterialization(asset_key=asset_key)
                    ),
                ),
            )
        )
        assert asset_key in storage.all_asset_keys()

        storage.wipe_asset(asset_key)
        storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=RUNLESS_RUN_ID,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    event_type_value=DagsterEventType.ASSET_WIPED.value,
                    job_name=RUNLESS_JOB_NAME,
                    event_specific_data=AssetWipedData(asset_key=asset_key, partition_keys=None),
                ),
            )
        )

        assert asset_key not in storage.all_asset_keys()
        assert storage.get_latest_materialization_events([asset_key]).get(asset_key) is None
