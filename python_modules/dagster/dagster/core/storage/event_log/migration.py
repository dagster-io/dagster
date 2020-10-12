import sqlalchemy as db
from tqdm import tqdm

from .schema import AssetKeyTable, SqlEventLogStorageTable


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


def migrate_asset_key_data(event_log_storage, print_fn=lambda _: None):
    """
    Utility method to build an asset key index from the data in existing event log records.
    Takes in event_log_storage, and a print_fn to keep track of progress.
    """
    from dagster.core.storage.event_log.sql_event_log import AssetAwareSqlEventLogStorage

    if not isinstance(event_log_storage, AssetAwareSqlEventLogStorage):
        return

    query = (
        db.select([SqlEventLogStorageTable.c.asset_key])
        .where(SqlEventLogStorageTable.c.asset_key != None)
        .group_by(SqlEventLogStorageTable.c.asset_key)
    )
    with event_log_storage.connect() as conn:
        print_fn("Querying event logs.")
        to_insert = conn.execute(query).fetchall()
        print_fn("Found {} records to index".format(len(to_insert)))
        for (asset_key,) in tqdm(to_insert):
            try:
                conn.execute(
                    AssetKeyTable.insert().values(  # pylint: disable=no-value-for-parameter
                        asset_key=asset_key
                    )
                )
            except db.exc.IntegrityError:
                # asset key already present
                pass
