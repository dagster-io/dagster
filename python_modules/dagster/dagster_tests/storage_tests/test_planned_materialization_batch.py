import asyncio
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import dagster as dg
import pytest
import sqlalchemy as db
from dagster._core.assets import AssetDetails
from dagster._core.events import AssetMaterializationPlannedData
from dagster._core.loader import LoadingContextForTest
from dagster._core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
    SqliteEventLogStorage,
)
from dagster._core.storage.event_log.base import EventLogStorage, PlannedMaterializationInfo
from dagster._core.storage.event_log.schema import AssetKeyTable, SqlEventLogStorageTable
from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster._serdes import serialize_value
from dagster_shared.serdes.errors import DeserializationError
from sqlalchemy import event as sqlalchemy_event


@pytest.fixture(params=["memory", "sqlite", "consolidated"])
def storage(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[SqlEventLogStorage]:
    if request.param == "memory":
        value = InMemoryEventLogStorage()
    elif request.param == "sqlite":
        value = SqliteEventLogStorage(str(tmp_path))
    else:
        value = ConsolidatedSqliteEventLogStorage(str(tmp_path))
    try:
        yield value
    finally:
        value.dispose()


def _plan(key: dg.AssetKey, run_id: str, timestamp: float = 200.0) -> dg.EventLogEntry:
    return dg.EventLogEntry(
        error_info=None,
        level="debug",
        user_message="",
        run_id=run_id,
        timestamp=timestamp,
        dagster_event=dg.DagsterEvent(
            dg.DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
            "job",
            event_specific_data=AssetMaterializationPlannedData(key),
        ),
    )


@pytest.mark.parametrize("requested", ["alias", "both", "wiped"])
def test_case_insensitive_plans_preserve_singular_parity(requested: str) -> None:
    storage = InMemoryEventLogStorage()
    try:
        with storage.index_connection() as conn:
            conn.execute(db.text("DROP TABLE event_logs"))
            conn.execute(
                db.text("""CREATE TABLE event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, run_id VARCHAR(255),
                event TEXT NOT NULL, dagster_event_type TEXT, timestamp TIMESTAMP,
                step_key TEXT, asset_key TEXT COLLATE NOCASE, partition TEXT
            )""")
            )
        upper, lower = dg.AssetKey("A"), dg.AssetKey("a")
        storage.store_event(_plan(upper, "upper", 200.0))
        keys = [lower] if requested == "alias" else [upper, lower, upper]
        if requested != "alias":
            storage.store_event(_plan(lower, "lower", 300.0))
        if requested == "wiped":
            # Wipes are per requested key, even when event_logs considers keys equal.
            with storage.index_connection() as conn:
                conn.execute(
                    AssetKeyTable.update()
                    .where(AssetKeyTable.c.asset_key == upper.to_string())
                    .values(
                        asset_details=serialize_value(AssetDetails(last_wipe_timestamp=300.0)),
                        wipe_timestamp=None,
                    )
                )
        expected = {key: storage.get_latest_planned_materialization_info(key) for key in keys}
        assert expected[lower] is not None
        if requested == "wiped":
            assert expected[upper] is None
        elif requested == "both":
            assert expected[upper] == expected[lower]
        with mock.patch.object(
            storage,
            "get_latest_planned_materialization_info",
            side_effect=AssertionError("singular read"),
        ):
            assert storage.get_latest_planned_materialization_info_for_keys(keys) == expected
    finally:
        storage.dispose()


def test_default_fallback_deduplicates_and_preserves_missing() -> None:
    backend = mock.Mock(spec=EventLogStorage)
    a, b = dg.AssetKey("a"), dg.AssetKey("b")
    info = PlannedMaterializationInfo(storage_id=9, run_id="run")
    backend.get_latest_planned_materialization_info.side_effect = [info, None]
    result = EventLogStorage.get_latest_planned_materialization_info_for_keys(backend, [a, b, a])
    assert result == {a: info, b: None}
    assert backend.get_latest_planned_materialization_info.call_args_list == [
        mock.call(a),
        mock.call(b),
    ]
    backend.get_latest_planned_materialization_info.reset_mock()
    assert EventLogStorage.get_latest_planned_materialization_info_for_keys(backend, []) == {}
    backend.get_latest_planned_materialization_info.assert_not_called()
    assert (
        "get_latest_planned_materialization_info_for_keys"
        not in EventLogStorage.__abstractmethods__
    )


@pytest.mark.asyncio
async def test_planned_loader_order_and_cache_boundaries() -> None:
    a, b, missing = [dg.AssetKey(name) for name in ["a", "b", "missing"]]
    with dg.DagsterInstance.ephemeral() as instance:
        storage = instance.event_log_storage
        storage.store_event(_plan(a, "a1"))
        storage.store_event(_plan(b, "b1"))
        context = LoadingContextForTest(instance)
        with mock.patch.object(
            storage,
            "get_latest_planned_materialization_info_for_keys",
            wraps=storage.get_latest_planned_materialization_info_for_keys,
        ) as batch:
            records = list(
                await PlannedMaterializationInfo.gen_many(context, iter([b, a, missing, a]))
            )
            assert [record.run_id if record else None for record in records] == [
                "b1",
                "a1",
                None,
                "a1",
            ]
            assert batch.call_count == 1
            await asyncio.gather(
                PlannedMaterializationInfo.gen(context, a),
                PlannedMaterializationInfo.gen(context, missing),
            )
            assert batch.call_count == 1
            storage.store_event(_plan(a, "a2"))
            cached = await PlannedMaterializationInfo.gen(context, a)
            assert cached is not None and cached.run_id == "a1"
            # The blocking and async caches intentionally have separate lifetimes.
            blocking = PlannedMaterializationInfo.blocking_get(context, a)
            assert blocking is not None and blocking.run_id == "a2"
            assert batch.call_count == 2
            fresh_context = LoadingContextForTest(instance)
            fresh = await PlannedMaterializationInfo.gen(fresh_context, a)
            assert fresh is not None and fresh.run_id == "a2"
            assert batch.call_count == 3


@pytest.mark.parametrize("count", [200, 201])
def test_batch_all_legacy_wipes_respects_sqlite_limits(
    storage: SqlEventLogStorage, count: int
) -> None:
    keys = [dg.AssetKey(f"wiped_{i}") for i in range(count)]
    for key in keys:
        storage.store_event(_plan(key, "run"))
    # Legacy databases may only have serialized AssetDetails, not a migrated wipe_timestamp.
    with storage.index_connection() as conn:
        conn.execute(
            AssetKeyTable.update().values(
                asset_details=serialize_value(AssetDetails(last_wipe_timestamp=200.0)),
                wipe_timestamp=None,
            )
        )
    statements = []
    parameter_counts = []

    def record_query(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)
            parameter_counts.append(len(parameters))

    sqlalchemy_event.listen(db.engine.Engine, "before_cursor_execute", record_query)
    try:
        with mock.patch.object(
            storage, "index_connection", wraps=storage.index_connection
        ) as connect:
            # Strict > wipe timestamp, including equality at the boundary.
            assert storage.get_latest_planned_materialization_info_for_keys(keys) == dict.fromkeys(
                keys
            )
            assert connect.call_count == 2 * ((count + 199) // 200)
    finally:
        sqlalchemy_event.remove(db.engine.Engine, "before_cursor_execute", record_query)
    assert len(statements) == 2 * ((count + 199) // 200)
    assert max(parameter_counts) < 999


@pytest.mark.parametrize(
    "bad_json", ["{broken", "3", serialize_value(AssetDetails(last_wipe_timestamp=200.0))]
)
def test_corrupt_latest_plan_matches_singular(storage: SqlEventLogStorage, bad_json: str) -> None:
    key = dg.AssetKey("corrupt")
    storage.store_event(_plan(key, "older"))
    storage.store_event(_plan(key, "newer"))
    newest = storage.get_latest_planned_materialization_info(key)
    assert newest is not None
    with storage.index_connection() as conn:
        conn.execute(
            SqlEventLogStorageTable.update()
            .where(SqlEventLogStorageTable.c.id == newest.storage_id)
            .values(event=bad_json)
        )
    if bad_json == "3":
        # Valid JSON of an unexpected type propagates, just as in the singular API.
        with pytest.raises(DeserializationError):
            storage.get_latest_planned_materialization_info(key)
        with pytest.raises(DeserializationError):
            storage.get_latest_planned_materialization_info_for_keys([key])
    else:
        assert storage.get_latest_planned_materialization_info(key) is None
        assert storage.get_latest_planned_materialization_info_for_keys([key]) == {key: None}


def test_sharded_sqlite_uses_asset_index_ids(storage: SqlEventLogStorage) -> None:
    if not isinstance(storage, SqliteEventLogStorage):
        pytest.skip("run-sharded SQLite only")
    key = dg.AssetKey("asset")
    # The first run has a larger local ID, but the second run has the newest index ID.
    for _ in range(5):
        storage.store_event(_plan(key, "first"))
    storage.store_event(_plan(key, "second"))
    result = storage.get_latest_planned_materialization_info_for_keys([key])[key]
    assert result is not None and result.run_id == "second"
    assert result == storage.get_latest_planned_materialization_info(key)
