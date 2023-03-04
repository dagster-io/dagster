"""add primary key cols

Revision ID: d9092588866f
Revises: e62c379ac8f4
Create Date: 2023-03-03 14:20:07.082211

"""
import sqlalchemy as db
from alembic import op
from dagster._core.storage.migration.utils import has_column, has_primary_key, has_table
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "d9092588866f"
down_revision = "e62c379ac8f4"
branch_labels = None
depends_on = None


def _should_create_primary_key(tablename):
    dialect = op.get_context().dialect.name

    if dialect == "sqlite":
        # Sqlite autogenerates primary keys using the rowid column, so we should skip primary key
        # generation for sqlite
        return False

    if dialect == "mysql":
        # Also, some instances of mysql might have invisible primary key generation turned on, which is
        # hard to detect. in an abundance of caution, we should not attempt to create a primary key
        # here and allow dbadmins to convert the unique id column to a primary key if they want to.
        # See https://dev.mysql.com/doc/refman/8.0/en/create-table-gipks.html
        return False

    # If the table already has a primary key, we should not create a new one
    return not has_primary_key(tablename)


def upgrade():
    if has_table("kvs") and not has_column("kvs", "id"):
        with op.batch_alter_table("kvs") as batch_op:
            batch_op.add_column(
                db.Column(
                    "id",
                    db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                    autoincrement=True,
                ),
            )
            if _should_create_primary_key("kvs"):
                batch_op.create_primary_key("kvs_pkey", ["id"])
            else:
                batch_op.create_unique_constraint("kvs_id_unique", ["id"])

    if has_table("instance_info") and not has_column("kvs", "id"):
        with op.batch_alter_table("instance_info") as batch_op:
            batch_op.add_column(
                db.Column(
                    "id",
                    db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                    autoincrement=True,
                ),
            )
            if _should_create_primary_key("instance_info"):
                batch_op.create_primary_key("instance_info_pkey", ["id"])
            else:
                batch_op.create_unique_constraint("instance_info_id_unique", ["id"])

    if has_table("daemon_heartbeats") and not has_column("daemon_heartbeats", "id"):
        with op.batch_alter_table("daemon_heartbeats") as batch_op:
            batch_op.add_column(
                db.Column(
                    "id",
                    db.BigInteger().with_variant(sqlite.INTEGER(), "sqlite"),
                    autoincrement=True,
                ),
            )
            if _should_create_primary_key("daemon_heartbeats"):
                batch_op.create_primary_key("daemon_heartbeats_pkey", ["id"])
            else:
                batch_op.create_unique_constraint("daemon_heartbeats_id_unique", ["id"])


def downgrade():
    pass
