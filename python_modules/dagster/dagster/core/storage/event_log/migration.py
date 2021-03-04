import sqlalchemy as db
from dagster import AssetKey
from dagster.core.events.log import EventRecord
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from tqdm import tqdm

SECONDARY_INDEX_ASSET_KEY = "asset_key_table"

REINDEX_DATA_MIGRATIONS = {
    SECONDARY_INDEX_ASSET_KEY: lambda: migrate_asset_key_data,
}


def migrate_event_log_data(instance=None):
    """
    Utility method to migrate the data in the existing event log records.  Reads every event log row
    reachable from the instance and reserializes it to event log storage.  Deserializing and then
    reserializing the event from storage allows for things like SQL column extraction, filling
    explicit default values, etc.
    """
    from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage

    event_log_storage = instance._event_storage  # pylint: disable=protected-access

    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    for run in instance.get_runs():
        event_records_by_id = event_log_storage.get_logs_for_run_by_log_id(run.run_id)
        for record_id, event in event_records_by_id.items():
            event_log_storage.update_event_log_record(record_id, event)


def migrate_asset_key_data(event_log_storage, print_fn=None):
    """
    Utility method to build an asset key index from the data in existing event log records.
    Takes in event_log_storage, and a print_fn to keep track of progress.
    """
    from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage
    from .schema import AssetKeyTable, SqlEventLogStorageTable

    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    query = (
        db.select([SqlEventLogStorageTable.c.asset_key])
        .where(SqlEventLogStorageTable.c.asset_key != None)
        .group_by(SqlEventLogStorageTable.c.asset_key)
    )
    with event_log_storage.index_connection() as conn:
        if print_fn:
            print_fn("Querying event logs.")
        to_insert = conn.execute(query).fetchall()
        if print_fn:
            print_fn("Found {} records to index".format(len(to_insert)))
            to_insert = tqdm(to_insert)

        for (asset_key,) in to_insert:
            try:
                conn.execute(
                    AssetKeyTable.insert().values(  # pylint: disable=no-value-for-parameter
                        asset_key=AssetKey.from_db_string(asset_key).to_string()
                    )
                )
            except db.exc.IntegrityError:
                # asset key already present
                pass


def sql_asset_event_generator(conn, cursor=None, batch_size=1000):
    from .schema import SqlEventLogStorageTable

    while True:
        query = db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event]).where(
            SqlEventLogStorageTable.c.asset_key != None
        )
        if cursor:
            query = query.where(SqlEventLogStorageTable.c.id < cursor)
        query = query.order_by(SqlEventLogStorageTable.c.id.desc()).limit(batch_size)
        fetched = conn.execute(query).fetchall()

        for (record_id, event_json) in fetched:
            cursor = record_id
            event_record = deserialize_json_to_dagster_namedtuple(event_json)
            if not isinstance(event_record, EventRecord):
                continue
            yield (record_id, event_record)

        if fetched < batch_size:
            break
