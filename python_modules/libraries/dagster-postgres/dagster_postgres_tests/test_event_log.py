import gc
import math
import time
from contextlib import contextmanager

import dagster_postgres.event_log.event_log as dagster_postgres_event_log
import objgraph
import pytest
import yaml
from dagster import AssetCheckKey, AssetKey, StaticPartitionsDefinition
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.event_log.sql_event_log import (
    ASSET_CHECK_PARTITION_INFO_BATCH_SIZE,
    ASSET_CHECK_PARTITION_INFO_MAX_BIND_PARAMS,
)
from dagster._core.storage.sql import stamp_alembic_rev
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster._core.utils import make_new_run_id
from dagster_postgres.event_log import PostgresEventLogStorage
from dagster_postgres.utils import pg_alembic_config
from sqlalchemy import event, inspect

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.event_log_storage import (
    TestEventLogStorage,
    _create_check_evaluation_event,
    _create_check_planned_event,
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

    def test_asset_check_partition_info_uses_single_batched_query(self, storage):
        check_keys = [
            AssetCheckKey(AssetKey(["asset_one"]), "check_one"),
            AssetCheckKey(AssetKey(["asset_two"]), "check_two"),
            AssetCheckKey(AssetKey(["asset_three"]), "check_three"),
        ]
        partitions_subset = StaticPartitionsDefinition(["a"]).subset_with_partition_keys(["a"])

        for check_key in check_keys:
            run_id = make_new_run_id()
            storage.store_event(
                _create_check_planned_event(run_id, check_key, partitions_subset=partitions_subset)
            )
            storage.store_event(
                _create_check_evaluation_event(run_id, check_key, passed=True, partition="a")
            )

        statements = []

        def _capture_statement(
            conn, cursor, statement, parameters, context, executemany
        ):
            statements.append(statement)

        event.listen(storage._engine, "before_cursor_execute", _capture_statement)
        try:
            storage.get_asset_check_partition_info(check_keys)
        finally:
            event.remove(storage._engine, "before_cursor_execute", _capture_statement)

        asset_check_selects = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith("SELECT")
            and "asset_check_executions" in statement
        ]
        assert len(asset_check_selects) == 1

    def test_asset_check_partition_info_uses_bounded_queries_for_large_batches(self, storage):
        check_keys = [
            AssetCheckKey(AssetKey([f"asset_{index}"]), f"check_{index}")
            for index in range(ASSET_CHECK_PARTITION_INFO_BATCH_SIZE + 200)
        ]
        partitions_subset = StaticPartitionsDefinition(["a"]).subset_with_partition_keys(["a"])

        for check_key in check_keys:
            run_id = make_new_run_id()
            storage.store_event(
                _create_check_planned_event(run_id, check_key, partitions_subset=partitions_subset)
            )
            storage.store_event(
                _create_check_evaluation_event(run_id, check_key, passed=True, partition="a")
            )

        statements = []

        def _capture_statement(
            conn, cursor, statement, parameters, context, executemany
        ):
            statements.append(statement)

        event.listen(storage._engine, "before_cursor_execute", _capture_statement)
        try:
            records = storage.get_asset_check_partition_info(check_keys)
        finally:
            event.remove(storage._engine, "before_cursor_execute", _capture_statement)

        assert len(records) == len(check_keys)

        asset_check_selects = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith("SELECT")
            and "asset_check_executions" in statement
        ]
        expected_batch_size = min(
            ASSET_CHECK_PARTITION_INFO_BATCH_SIZE,
            ASSET_CHECK_PARTITION_INFO_MAX_BIND_PARAMS // 3,
        )
        assert len(asset_check_selects) == math.ceil(len(check_keys) / expected_batch_size)

    def test_asset_check_partition_info_uses_bounded_queries_for_large_filtered_batches(
        self, storage
    ):
        check_keys = [
            AssetCheckKey(AssetKey([f"asset_{index}"]), f"check_{index}")
            for index in range(600)
        ]
        partition_keys = ["a", *[f"unused_{index}" for index in range(250)]]
        partitions_subset = StaticPartitionsDefinition(["a"]).subset_with_partition_keys(["a"])

        for check_key in check_keys:
            run_id = make_new_run_id()
            storage.store_event(
                _create_check_planned_event(run_id, check_key, partitions_subset=partitions_subset)
            )
            storage.store_event(
                _create_check_evaluation_event(run_id, check_key, passed=True, partition="a")
            )

        statements = []

        def _capture_statement(
            conn, cursor, statement, parameters, context, executemany
        ):
            statements.append(statement)

        event.listen(storage._engine, "before_cursor_execute", _capture_statement)
        try:
            records = storage.get_asset_check_partition_info(
                check_keys,
                partition_keys=partition_keys,
            )
        finally:
            event.remove(storage._engine, "before_cursor_execute", _capture_statement)

        assert len(records) == len(check_keys)

        asset_check_selects = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith("SELECT")
            and "asset_check_executions" in statement
        ]
        expected_batch_size = min(
            ASSET_CHECK_PARTITION_INFO_BATCH_SIZE,
            (ASSET_CHECK_PARTITION_INFO_MAX_BIND_PARAMS - (2 * len(partition_keys))) // 3,
        )
        assert len(asset_check_selects) == math.ceil(len(check_keys) / expected_batch_size)

    def test_asset_check_partition_latest_index_migration(self, instance):
        event_log_storage = instance.event_log_storage
        assert isinstance(event_log_storage, PostgresEventLogStorage)

        with event_log_storage.index_connection() as conn:
            conn.exec_driver_sql("DROP INDEX IF EXISTS idx_asset_check_executions_partition_latest")
            stamp_alembic_rev(
                pg_alembic_config(dagster_postgres_event_log.__file__),
                conn,
                "29b539ebc72a",
            )

        instance.upgrade()

        indexes = {
            index["name"]
            for index in inspect(event_log_storage._engine).get_indexes(
                "asset_check_executions"
            )
        }
        assert "idx_asset_check_executions_partition_latest" in indexes

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

        with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
            from_url = from_url_instance._event_storage  # noqa: SLF001

            with instance_for_test(overrides=yaml.safe_load(explicit_cfg)) as explicit_instance:
                from_explicit = explicit_instance._event_storage  # noqa: SLF001

                assert from_url.postgres_url == from_explicit.postgres_url  # pyright: ignore[reportAttributeAccessIssue]
