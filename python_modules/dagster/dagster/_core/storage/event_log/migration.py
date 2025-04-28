from typing import NamedTuple

import sqlalchemy as db
from dagster_shared.serdes import deserialize_value
from tqdm import tqdm

from dagster._core.assets import AssetDetails
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._time import datetime_from_timestamp

SECONDARY_INDEX_ASSET_KEY = "asset_key_table"  # builds the asset key table from the event log
ASSET_KEY_INDEX_COLS = "asset_key_index_columns"  # extracts index columns from the asset_keys table

EVENT_LOG_DATA_MIGRATIONS = {
    SECONDARY_INDEX_ASSET_KEY: lambda: migrate_asset_key_data,
}
ASSET_DATA_MIGRATIONS = {ASSET_KEY_INDEX_COLS: lambda: migrate_asset_keys_index_columns}


def migrate_event_log_data(instance=None):
    """Utility method to migrate the data in the existing event log records.  Reads every event log row
    reachable from the instance and reserializes it to event log storage.  Deserializing and then
    reserializing the event from storage allows for things like SQL column extraction, filling
    explicit default values, etc.
    """
    from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage

    event_log_storage = instance._event_storage  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]

    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    for run in instance.get_runs():  # pyright: ignore[reportOptionalMemberAccess]
        for record in event_log_storage.get_records_for_run(run.run_id).records:
            event_log_storage.update_event_log_record(record.storage_id, record.event_log_entry)


def migrate_asset_key_data(event_log_storage, print_fn=None):
    """Utility method to build an asset key index from the data in existing event log records.
    Takes in event_log_storage, and a print_fn to keep track of progress.
    """
    from dagster._core.definitions.events import AssetKey
    from dagster._core.storage.event_log.schema import AssetKeyTable, SqlEventLogStorageTable
    from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage

    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    query = (
        db_select([SqlEventLogStorageTable.c.asset_key])
        .where(SqlEventLogStorageTable.c.asset_key != None)  # noqa: E711
        .group_by(SqlEventLogStorageTable.c.asset_key)
    )
    with event_log_storage.index_connection() as conn:
        if print_fn:
            print_fn("Querying event logs.")
        to_insert = conn.execute(query).fetchall()
        if print_fn:
            print_fn(f"Found {len(to_insert)} records to index")
            to_insert = tqdm(to_insert)

        for (asset_key,) in to_insert:
            try:
                conn.execute(
                    AssetKeyTable.insert().values(
                        asset_key=AssetKey.from_db_string(asset_key).to_string()  # pyright: ignore[reportOptionalMemberAccess]
                    )
                )
            except db.exc.IntegrityError:  # pyright: ignore[reportAttributeAccessIssue]
                # asset key already present
                pass


def migrate_asset_keys_index_columns(event_log_storage, print_fn=None):
    from dagster._core.definitions.events import AssetKey
    from dagster._core.storage.event_log.schema import AssetKeyTable, SqlEventLogStorageTable
    from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage
    from dagster._serdes import serialize_value

    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    with event_log_storage.index_connection() as conn:
        if print_fn:
            print_fn("Querying asset keys.")
        results = conn.execute(
            db_select(
                [
                    AssetKeyTable.c.asset_key,
                    AssetKeyTable.c.asset_details,
                    AssetKeyTable.c.last_materialization,
                ]
            )
        ).fetchall()

        if print_fn:
            print_fn(f"Found {len(results)} assets to reindex.")
            results = tqdm(results)

        for row in results:
            asset_key_str, asset_details_str, last_materialization_str = row
            wipe_timestamp = None
            event = None

            asset_key = AssetKey.from_db_string(asset_key_str)

            if asset_details_str:
                asset_details = deserialize_value(asset_details_str, AssetDetails)
                wipe_timestamp = asset_details.last_wipe_timestamp if asset_details else None

            if last_materialization_str:
                event_or_materialization = deserialize_value(last_materialization_str, NamedTuple)

                if isinstance(event_or_materialization, EventLogEntry):
                    event = event_or_materialization

            if not event:
                materialization_query = (
                    db_select([SqlEventLogStorageTable.c.event])
                    .where(
                        SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
                    )
                    .order_by(SqlEventLogStorageTable.c.timestamp.desc())
                    .limit(1)
                )
                materialization_row = conn.execute(materialization_query).fetchone()
                if materialization_row:
                    event = deserialize_value(materialization_row[0], NamedTuple)  # pyright: ignore[reportCallIssue,reportArgumentType]

            if not event:
                # this must be a wiped asset
                conn.execute(
                    AssetKeyTable.update()
                    .values(
                        last_materialization=None,
                        last_materialization_timestamp=None,
                        wipe_timestamp=(
                            datetime_from_timestamp(wipe_timestamp) if wipe_timestamp else None
                        ),
                    )
                    .where(
                        AssetKeyTable.c.asset_key == asset_key.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
                    )
                )
            else:
                conn.execute(
                    AssetKeyTable.update()
                    .values(
                        last_materialization=serialize_value(event),
                        last_materialization_timestamp=datetime_from_timestamp(event.timestamp),
                        wipe_timestamp=(
                            datetime_from_timestamp(wipe_timestamp) if wipe_timestamp else None
                        ),
                    )
                    .where(
                        AssetKeyTable.c.asset_key == asset_key.to_string(),  # pyright: ignore[reportOptionalMemberAccess]
                    )
                )


def sql_asset_event_generator(conn, cursor=None, batch_size=1000):
    from dagster._core.storage.event_log.schema import SqlEventLogStorageTable

    while True:
        query = db_select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event]).where(
            SqlEventLogStorageTable.c.asset_key != None  # noqa: E711
        )
        if cursor:
            query = query.where(SqlEventLogStorageTable.c.id < cursor)
        query = query.order_by(SqlEventLogStorageTable.c.id.desc()).limit(batch_size)
        fetched = conn.execute(query).fetchall()

        for record_id, event_json in fetched:
            cursor = record_id
            event_record = deserialize_value(event_json, NamedTuple)
            if not isinstance(event_record, EventLogEntry):
                continue
            yield (record_id, event_record)

        if fetched < batch_size:
            break
