from contextlib import contextmanager

import sqlalchemy as db
from alembic import op
from dagster import check
from sqlalchemy.engine import reflection


def get_inspector():
    # pylint: disable=no-member
    bind = op.get_context().bind
    return reflection.Inspector.from_engine(bind)


def get_table_names():
    return get_inspector().get_table_names()


def has_table(table_name):
    return table_name in get_table_names()


def has_column(table_name, column_name):
    if not has_table(table_name):
        return False
    columns = [x.get("name") for x in get_inspector().get_columns(table_name)]
    return column_name in columns


_UPGRADING_INSTANCE = None


@contextmanager
def upgrading_instance(instance):
    global _UPGRADING_INSTANCE  # pylint: disable=global-statement
    check.invariant(_UPGRADING_INSTANCE is None, "update already in progress")
    try:
        _UPGRADING_INSTANCE = instance
        yield
    finally:
        _UPGRADING_INSTANCE = None


def get_currently_upgrading_instance():
    global _UPGRADING_INSTANCE  # pylint: disable=global-statement
    check.invariant(_UPGRADING_INSTANCE is not None, "currently upgrading instance not set")
    return _UPGRADING_INSTANCE


# alembic magic breaks pylint
# pylint: disable=no-member

# These intentionally use the schema at the time of the 0.10.0 release, to be used
# during the 0.10.0 new tables migration


def create_0_10_0_run_tables():
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


def create_0_10_0_event_log_tables():
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


def create_0_10_0_schedule_tables():
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


def create_bulk_actions_table():
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
