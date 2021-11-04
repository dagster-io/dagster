"""Base revision for SQL-backed event log storage

Revision ID: 567bc23fd1ac
Revises: 
Create Date: 2019-11-21 09:59:57.028730

"""

# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "567bc23fd1ac"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This is our root migration, and we don't have a common base. Before this revision, sqlite- and
    # postgres-based event logs had different schemas. The conditionality below is to deal with dev
    # databases that might not have been stamped by Alembic.
    bind = op.get_context().bind

    inspector = reflection.Inspector.from_engine(bind)

    if "postgresql" not in inspector.dialect.dialect_description:
        raise Exception(
            "Bailing: refusing to run a migration for postgres-backed event log storage against "
            "a non-postgres database of dialect {dialect}".format(
                dialect=inspector.dialect.dialect_description
            )
        )

    has_tables = inspector.get_table_names()

    if "event_log" in has_tables:
        op.drop_column(
            table_name="event_log", column_name="id",
        )
        op.alter_column(
            table_name="event_log",
            column_name="run_id",
            nullable=True,
            type_=sa.types.String(255),
            existing_type=sa.types.VARCHAR(255),
        )
        op.alter_column(
            table_name="event_log",
            column_name="event_body",
            nullable=False,
            new_column_name="event",
            type_=sa.types.Text,
            existing_type=sa.types.VARCHAR,
        )
        op.add_column(table_name="event_log", column=Column("dagster_event_type", sa.types.Text))
        op.add_column(table_name="event_log", column=Column("timestamp", sa.types.TIMESTAMP))
        op.execute(
            "update event_log\n"
            "set\n"
            "  dagster_event_type = event::json->'dagster_event'->>'event_type_value',\n"
            "  timestamp = to_timestamp((event::json->>'timestamp')::double precision)"
        )
        # op.execute('''select setval(pg_get_serial_sequence('event_logs', 'id'), greatest(select max(id) from event_log, select max(id) from event_logs))''')
        op.execute(
            "insert into event_logs (run_id, event, dagster_event_type, timestamp) "
            "select run_id, event, dagster_event_type, timestamp "
            "from event_log"
        )
        op.drop_table("event_log")


def downgrade():
    raise Exception("Base revision, no downgrade is possible")
