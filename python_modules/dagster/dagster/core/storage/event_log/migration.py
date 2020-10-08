from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage


def migrate_event_log_data(instance=None):
    """
    Utility method to migrate the data in the existing event log records.  Reads every event log row
    reachable from the instance and reserializes it to event log storage.  Deserializing and then
    reserializing the event from storage allows for things like SQL column extraction, filling
    explicit default values, etc.
    """
    event_log_storage = instance._event_storage  # pylint: disable=protected-access
    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    for run in instance.get_runs():
        event_records_by_id = event_log_storage.get_logs_for_run_by_log_id(run.run_id)
        for record_id, event in event_records_by_id.items():
            event_log_storage.update_event_log_record(record_id, event)
