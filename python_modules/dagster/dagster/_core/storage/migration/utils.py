from contextlib import contextmanager
from typing import Iterator, Sequence

import sqlalchemy as db
from alembic import op
from sqlalchemy import inspect

import dagster._check as check
from dagster._core.instance import DagsterInstance
from dagster._core.storage.sql import get_current_timestamp


def get_inspector():
    return inspect(op.get_bind())


def get_table_names() -> Sequence[str]:
    return get_inspector().get_table_names()


def has_table(table_name: str) -> bool:
    return table_name in get_table_names()


def has_column(table_name: str, column_name: str) -> bool:
    if not has_table(table_name):
        return False
    columns = [x.get("name") for x in get_inspector().get_columns(table_name)]
    return column_name in columns


def has_index(table_name: str, index_name: str) -> bool:
    if not has_table(table_name):
        return False
    indexes = [x.get("name") for x in get_inspector().get_indexes(table_name)]
    return index_name in indexes


def get_primary_key(table_name):
    return get_inspector().get_pk_constraint(table_name)


_UPGRADING_INSTANCE = None


@contextmanager
def upgrading_instance(instance: DagsterInstance) -> Iterator[None]:
    global _UPGRADING_INSTANCE  # noqa: PLW0603
    check.invariant(_UPGRADING_INSTANCE is None, "update already in progress")
    try:
        _UPGRADING_INSTANCE = instance  # noqa: PLW0603
        yield
    finally:
        _UPGRADING_INSTANCE = None


def get_currently_upgrading_instance() -> DagsterInstance:
    global _UPGRADING_INSTANCE  # noqa: PLW0602
    check.invariant(_UPGRADING_INSTANCE is not None, "currently upgrading instance not set")
    return _UPGRADING_INSTANCE  # type: ignore  # (possible none)


# alembic magic breaks pylint


# These intentionally use the schema at the time of the 0.10.0 release, to be used
# during the 0.10.0 new tables migration


def create_0_10_0_run_tables() -> None:
    if not has_table("runs"):
        return

    if not has_table("secondary_indexes"):
        op.create_table(
            "secondary_indexes",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("name", db.String, unique=True),
            db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
            db.Column("migration_completed", db.DateTime),
        )

    if not has_table("daemon_heartbeats"):
        op.create_table(
            "daemon_heartbeats",
            db.Column("daemon_type", db.String(255), unique=True, nullable=False),
            db.Column("daemon_id", db.String(255)),
            db.Column("timestamp", db.types.TIMESTAMP, nullable=False),
            db.Column("body", db.Text),
        )


def create_0_10_0_event_log_tables() -> None:
    if not has_table("event_logs"):
        return

    if not has_table("secondary_indexes"):
        op.create_table(
            "secondary_indexes",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("name", db.String, unique=True),
            db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
            db.Column("migration_completed", db.DateTime),
        )

    if not has_table("asset_keys"):
        op.create_table(
            "asset_keys",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("asset_key", db.String, unique=True),
            db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
        )


def create_0_10_0_schedule_tables() -> None:
    if not has_table("schedules") and not has_table("jobs"):
        return

    if not has_table("jobs"):
        op.create_table(
            "jobs",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("job_origin_id", db.String(255), unique=True),
            db.Column("repository_origin_id", db.String(255)),
            db.Column("status", db.String(63)),
            db.Column("job_type", db.String(63), index=True),
            db.Column("job_body", db.String),
            db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
            db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
        )

    if not has_table("job_ticks"):
        op.create_table(
            "job_ticks",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("job_origin_id", db.String(255), index=True),
            db.Column("status", db.String(63)),
            db.Column("type", db.String(63)),
            db.Column("timestamp", db.types.TIMESTAMP),
            db.Column("tick_body", db.String),
            db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
            db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "idx_job_tick_status", "job_ticks", ["job_origin_id", "status"], unique=False
        )
        op.create_index(
            "idx_job_tick_timestamp", "job_ticks", ["job_origin_id", "timestamp"], unique=False
        )

    if has_table("schedules"):
        op.drop_table("schedules")

    if has_table("schedule_ticks"):
        op.drop_table("schedule_ticks")


def create_bulk_actions_table() -> None:
    if not has_table("runs"):
        return

    if not has_table("bulk_actions"):
        op.create_table(
            "bulk_actions",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("key", db.String(32), unique=True, nullable=False),
            db.Column("status", db.String(255), nullable=False),
            db.Column("timestamp", db.types.TIMESTAMP, nullable=False),
            db.Column("body", db.Text),
        )

        op.create_index("idx_bulk_actions_key", "bulk_actions", ["key"], unique=True)
        op.create_index("idx_bulk_actions_status", "bulk_actions", ["status"], unique=False)


def add_asset_materialization_columns() -> None:
    if not has_table("asset_keys"):
        return

    if has_column("asset_keys", "last_materialization"):
        return

    op.add_column("asset_keys", db.Column("last_materialization", db.Text))
    op.add_column("asset_keys", db.Column("last_run_id", db.String(255)))


def add_asset_details_column() -> None:
    if not has_table("asset_keys"):
        return

    if has_column("asset_keys", "asset_details"):
        return

    op.add_column("asset_keys", db.Column("asset_details", db.Text))


def extract_asset_keys_idx_columns() -> None:
    if not has_table("asset_keys"):
        return

    if has_column("asset_keys", "wipe_timestamp"):
        return

    # add timestamp, tags columns to avoid event deserialization
    op.add_column("asset_keys", db.Column("wipe_timestamp", db.types.TIMESTAMP))
    op.add_column("asset_keys", db.Column("last_materialization_timestamp", db.types.TIMESTAMP))
    op.add_column("asset_keys", db.Column("tags", db.TEXT))


def create_event_log_event_idx() -> None:
    if not has_table("event_logs"):
        return

    if has_index("event_logs", "idx_event_type"):
        return

    op.create_index(
        "idx_event_type",
        "event_logs",
        ["dagster_event_type", "id"],
        mysql_length={"dagster_event_type": 64},
    )


def create_run_range_indices() -> None:
    if not has_table("runs"):
        return

    if has_index("runs", "idx_run_range"):
        return

    op.create_index(
        "idx_run_range",
        "runs",
        ["status", "update_timestamp", "create_timestamp"],
        unique=False,
        mysql_length={
            "status": 32,
            "update_timestamp": 8,
            "create_timestamp": 8,
        },
    )


def add_run_record_start_end_timestamps() -> None:
    if not has_table("runs"):
        return

    if has_column("runs", "start_time"):
        return

    op.add_column("runs", db.Column("start_time", db.Float))
    op.add_column("runs", db.Column("end_time", db.Float))


def drop_run_record_start_end_timestamps() -> None:
    if not has_table("runs"):
        return

    if not has_column("runs", "start_time"):
        return

    op.drop_column("runs", "start_time")
    op.drop_column("runs", "end_time")


def create_schedule_secondary_index_table() -> None:
    if not has_table("jobs"):
        return

    if not has_table("secondary_indexes"):
        op.create_table(
            "secondary_indexes",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("name", db.String, unique=True),
            db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
            db.Column("migration_completed", db.DateTime),
        )


def create_instigators_table() -> None:
    if not has_table("instigators") and not has_table("jobs"):
        # not a schedule storage db
        return

    if not has_table("instigators"):
        op.create_table(
            "instigators",
            db.Column("id", db.Integer, primary_key=True, autoincrement=True),
            db.Column("selector_id", db.String(255), unique=True),
            db.Column("repository_selector_id", db.String(255)),
            db.Column("status", db.String(63)),
            db.Column("instigator_type", db.String(63), index=True),
            db.Column("instigator_body", db.Text),
            db.Column("create_timestamp", db.DateTime, server_default=get_current_timestamp()),
            db.Column("update_timestamp", db.DateTime, server_default=get_current_timestamp()),
        )

    if not has_column("jobs", "selector_id"):
        op.add_column("jobs", db.Column("selector_id", db.String(255)))

    if not has_column("job_ticks", "selector_id"):
        op.add_column("job_ticks", db.Column("selector_id", db.String(255)))


def create_tick_selector_index() -> None:
    if not has_table("job_ticks"):
        return

    if has_index("job_ticks", "idx_tick_selector_timestamp"):
        return

    op.create_index(
        "idx_tick_selector_timestamp", "job_ticks", ["selector_id", "timestamp"], unique=False
    )


def add_id_based_event_indices() -> None:
    if not has_table("event_logs"):
        return

    if not has_index("event_logs", "idx_events_by_run_id"):
        op.create_index(
            "idx_events_by_run_id",
            "event_logs",
            ["run_id", "id"],
            postgresql_concurrently=True,
            mysql_length={"run_id": 64},
        )
        if has_index("event_logs", "idx_run_id"):
            op.drop_index(
                "idx_run_id",
                "event_logs",
                postgresql_concurrently=True,
            )

    if not has_index("event_logs", "idx_events_by_asset"):
        op.create_index(
            "idx_events_by_asset",
            "event_logs",
            ["asset_key", "dagster_event_type", "id"],
            postgresql_concurrently=True,
            postgresql_where=db.text("asset_key IS NOT NULL"),
            mysql_length={"asset_key": 64, "dagster_event_type": 64},
        )
        if has_index("event_logs", "idx_asset_key"):
            op.drop_index(
                "idx_asset_key",
                "event_logs",
                postgresql_concurrently=True,
            )

    if not has_index("event_logs", "idx_events_by_asset_partition"):
        op.create_index(
            "idx_events_by_asset_partition",
            "event_logs",
            ["asset_key", "dagster_event_type", "partition", "id"],
            postgresql_concurrently=True,
            postgresql_where=db.text("asset_key IS NOT NULL AND partition IS NOT NULL"),
            mysql_length={"asset_key": 64, "dagster_event_type": 64, "partition": 64},
        )
        if has_index("event_logs", "idx_asset_partition"):
            op.drop_index(
                "idx_asset_partition",
                "event_logs",
                postgresql_concurrently=True,
            )


def drop_id_based_event_indices() -> None:
    if not has_table("event_logs"):
        return

    if not has_index("event_logs", "idx_asset_partition"):
        op.create_index(
            "idx_asset_partition",
            "event_logs",
            ["asset_key", "partition"],
            unique=False,
            postgresql_concurrently=True,
            mysql_length=64,
        )
        if has_index("event_logs", "idx_events_by_asset_partition"):
            op.drop_index(
                "idx_events_by_asset_partition", "event_logs", postgresql_concurrently=True
            )

    if not has_index("event_logs", "idx_asset_key"):
        op.create_index(
            "idx_asset_key",
            "event_logs",
            ["asset_key"],
            unique=False,
            postgresql_concurrently=True,
            mysql_length=64,
        )

        if has_index("event_logs", "idx_events_by_asset"):
            op.drop_index("idx_events_by_asset", "event_logs", postgresql_concurrently=True)

    if not has_index("event_logs", "idx_run_id"):
        op.create_index(
            "idx_run_id",
            "event_logs",
            ["run_id"],
            unique=False,
            postgresql_concurrently=True,
            mysql_length=64,
        )
        if has_index("event_logs", "idx_events_by_run_id"):
            op.drop_index(
                "idx_events_by_run_id",
                "event_logs",
                postgresql_concurrently=True,
            )


def add_cached_status_data_column() -> None:
    if not has_table("asset_keys"):
        return

    if has_column("asset_keys", "cached_status_data"):
        return

    op.add_column("asset_keys", db.Column("cached_status_data", db.Text))


def add_run_job_index() -> None:
    if not has_table("runs"):
        return

    if not has_index("runs", "idx_runs_by_job"):
        op.create_index(
            "idx_runs_by_job",
            "runs",
            ["pipeline_name", "id"],
            unique=False,
            postgresql_concurrently=True,
            mysql_length={
                "pipeline_name": 512,
            },
        )


def drop_run_job_index() -> None:
    if not has_table("runs"):
        return

    if has_index("runs", "idx_runs_by_job"):
        op.drop_index(
            "idx_runs_by_job",
            "runs",
            postgresql_concurrently=True,
        )
