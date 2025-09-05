"""Migration logic for populating asset_checks and asset_check_partitions tables from historical data."""

import sqlalchemy as db
import sqlalchemy.exc as db_exc

from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.event_log.schema import AssetCheckExecutionsTable, AssetChecksTable
from dagster._core.storage.sqlalchemy_compat import db_fetch_mappings, db_select
from dagster._time import datetime_from_timestamp

BATCH_SIZE = 1000


def migrate_asset_check_summary_data(event_log_storage, print_fn=None):
    """Build asset_checks and asset_check_partitions tables from existing asset_check_executions data."""
    from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage

    if not isinstance(event_log_storage, SqlEventLogStorage):
        return

    if not (
        event_log_storage.has_table("asset_checks")
        and event_log_storage.has_table("asset_check_partitions")
    ):
        raise Exception(
            "Required tables do not exist for asset check summary data migration. Run `dagster instance migrate` to create the necessary tables."
        )

    with event_log_storage.index_connection() as conn:
        if print_fn:
            print_fn("Starting asset check summary data migration...")

        total_executions = conn.execute(
            db_select([db.func.count()]).select_from(AssetCheckExecutionsTable)
        ).scalar()

        if print_fn:
            print_fn(f"Processing {total_executions} asset check execution records...")

        cursor = 0
        count = 0

        # AssetCheckKey -> {latest_execution_id, latest_run_id, latest_completed_id, first_timestamp, latest_timestamp}
        check_latest_data = {}

        while True:
            execution_query = (
                db_select(
                    [
                        AssetCheckExecutionsTable.c.id,
                        AssetCheckExecutionsTable.c.asset_key,
                        AssetCheckExecutionsTable.c.check_name,
                        AssetCheckExecutionsTable.c.partition,
                        AssetCheckExecutionsTable.c.run_id,
                        AssetCheckExecutionsTable.c.execution_status,
                        AssetCheckExecutionsTable.c.create_timestamp,
                    ]
                )
                .order_by(AssetCheckExecutionsTable.c.id)
                .limit(BATCH_SIZE)
            )
            if cursor:
                execution_query = execution_query.where(AssetCheckExecutionsTable.c.id > cursor)

            executions = list(db_fetch_mappings(conn, execution_query))
            if not executions:
                break

            if print_fn:
                print_fn(
                    f"Processing batch {count // BATCH_SIZE + 1} ({len(executions)} executions)..."
                )

            for execution in executions:
                asset_key = AssetKey.from_db_string(execution["asset_key"])
                if not asset_key:
                    continue
                check_key = AssetCheckKey(asset_key=asset_key, name=execution["check_name"])

                execution_id = execution["id"]
                run_id = execution["run_id"]
                status = AssetCheckExecutionRecordStatus(execution["execution_status"])
                timestamp = execution["create_timestamp"]

                if check_key not in check_latest_data:
                    check_latest_data[check_key] = {
                        "latest_execution_id": execution_id,
                        "latest_run_id": run_id,
                        "latest_completed_id": execution_id
                        if status
                        in {
                            AssetCheckExecutionRecordStatus.SUCCEEDED,
                            AssetCheckExecutionRecordStatus.FAILED,
                        }
                        else None,
                        "first_timestamp": timestamp,
                        "latest_timestamp": timestamp,
                    }
                else:
                    data = check_latest_data[check_key]
                    data["latest_execution_id"] = execution_id
                    data["latest_run_id"] = run_id
                    data["latest_timestamp"] = timestamp

                    if status in {
                        AssetCheckExecutionRecordStatus.SUCCEEDED,
                        AssetCheckExecutionRecordStatus.FAILED,
                    }:
                        data["latest_completed_id"] = execution_id

                cursor = execution_id
            count += len(executions)

        if print_fn:
            print_fn(f"Writing {len(check_latest_data)} asset checks to database...")

        # Write asset_checks rows
        for check_key, data in check_latest_data.items():
            try:
                conn.execute(
                    AssetChecksTable.insert().values(
                        asset_key=check_key.asset_key.to_string(),
                        check_name=check_key.name,
                        cached_check_status_data=None,
                        subset_cache_event_id=None,
                        last_execution_record_id=data["latest_execution_id"],
                        last_run_id=data["latest_run_id"],
                        last_completed_execution_record_id=data["latest_completed_id"],
                        created_timestamp=datetime_from_timestamp(data["first_timestamp"]),
                        updated_timestamp=datetime_from_timestamp(data["latest_timestamp"]),
                    )
                )
            except db_exc.IntegrityError:
                pass

        if print_fn:
            print_fn("Asset check summary data migration completed successfully.")
