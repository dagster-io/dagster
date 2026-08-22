"""Tests for the SQL Server alembic tree and its relationship to the one in dagster core.

dagster-mssql ships its own revision tree, so it does not pick up new core migrations
automatically.  The failure that causes is silent by construction: a fresh deployment
builds its schema with ``create_all()`` and is always correct, so a missing migration only
ever hurts deployments that upgrade, and only at the point some query hits a column that
was never added.

``TestCoreRevisionParity`` is the tripwire for that.  The rest of the module checks the
properties the tree itself has to hold, against a real server.
"""

import pytest
import sqlalchemy as db
from alembic.script import ScriptDirectory
from dagster._core.storage.event_log.schema import SqlEventLogStorageMetadata
from dagster._core.storage.runs.schema import RunStorageSqlMetadata
from dagster._core.storage.schedules.schema import ScheduleStorageSqlMetadata
from dagster._core.storage.sql import get_alembic_config
from dagster._utils.test.mssql_instance import TestMSSQLInstance
from dagster_mssql.alembic import CORE_REVISIONS_NOT_APPLICABLE, SYNCED_TO_CORE_REVISION
from dagster_mssql.event_log import MSSQLEventLogStorage
from dagster_mssql.run_storage import MSSQLRunStorage
from dagster_mssql.schedule_storage import MSSQLScheduleStorage
from dagster_mssql.utils import mssql_alembic_config


def _core_script_directory() -> ScriptDirectory:
    import dagster._core.storage.runs.sql_run_storage as core_run_storage

    return ScriptDirectory.from_config(
        get_alembic_config(core_run_storage.__file__, config_path="../alembic/alembic.ini")
    )


def _mssql_script_directory() -> ScriptDirectory:
    import dagster_mssql.run_storage.run_storage as mssql_run_storage

    return ScriptDirectory.from_config(mssql_alembic_config(mssql_run_storage.__file__))


class TestCoreRevisionParity:
    """dagster core's tree must not have moved past what this package was reconciled to.

    When this fails it is not a broken test -- it means core gained a migration that
    SQL Server deployments will not receive. See `dagster_mssql/alembic/__init__.py` for
    what to do about it.
    """

    def test_core_head_has_not_moved(self):
        core = _core_script_directory()
        heads = core.get_heads()

        assert len(heads) == 1, (
            f"dagster core's alembic tree has {len(heads)} heads ({heads}); it is expected"
            " to have exactly one. A branch was introduced upstream and the SQL Server"
            " tree needs to be reconciled against each head."
        )

        if heads[0] == SYNCED_TO_CORE_REVISION:
            return

        # Name the revisions that appeared, so the failure says what has to be looked at
        # rather than just that two strings differ.
        new_revisions = [
            f"  {rev.revision}  {rev.doc}"
            for rev in core.walk_revisions(base=SYNCED_TO_CORE_REVISION, head=heads[0])
            if rev.revision != SYNCED_TO_CORE_REVISION
        ]
        raise AssertionError(
            "dagster core added alembic revisions that the SQL Server tree has not been"
            " reconciled against:\n" + "\n".join(reversed(new_revisions)) + "\n\n"
            "SQL Server deployments running `dagster instance migrate` will NOT receive"
            " these. For each one, either add an equivalent revision under"
            " dagster_mssql/alembic/versions/, or record in CORE_REVISIONS_NOT_APPLICABLE"
            " why it does not apply -- then advance SYNCED_TO_CORE_REVISION in"
            " dagster_mssql/alembic/__init__.py."
        )

    def test_excused_revisions_exist_in_core(self):
        """Guards against a stale excuse outliving the revision it was written for."""
        core = _core_script_directory()
        for revision, reason in CORE_REVISIONS_NOT_APPLICABLE.items():
            assert core.get_revision(revision) is not None, (
                f"{revision} is recorded as not-applicable but is not in core's tree"
            )
            assert reason.strip(), f"{revision} is excused without a reason"


class TestMSSQLTreeShape:
    def test_single_head(self):
        heads = _mssql_script_directory().get_heads()
        assert len(heads) == 1, f"the SQL Server tree should have one head, found {heads}"

    def test_revisions_are_reachable_from_base(self):
        mssql = _mssql_script_directory()
        head = mssql.get_heads()[0]
        walked = {rev.revision for rev in mssql.walk_revisions(base="base", head=head)}
        all_revisions = {rev.revision for rev in mssql.walk_revisions()}
        assert walked == all_revisions, (
            f"revisions unreachable from base: {sorted(all_revisions - walked)}"
        )


@pytest.fixture(scope="module")
def storages(conn_string):
    """One clean instance of each of the three storages, sharing a database."""
    return {
        "run": MSSQLRunStorage.create_clean_storage(conn_string),
        "event_log": MSSQLEventLogStorage.create_clean_storage(conn_string),
        "schedule": MSSQLScheduleStorage.create_clean_storage(conn_string),
    }


METADATA_BY_STORAGE = {
    "run": RunStorageSqlMetadata,
    "event_log": SqlEventLogStorageMetadata,
    "schedule": ScheduleStorageSqlMetadata,
}


def _connect(storage):
    # SqlEventLogStorage spells this `_connect`; the other two spell it `connect`.
    return getattr(storage, "connect", None) or storage._connect  # noqa: SLF001


class TestFreshDatabase:
    def test_stamped_at_head(self, storages):
        """create_all() + stamp must leave every storage at the tree's head.

        If it stamped anything else, the next `dagster instance migrate` would try to
        replay revisions against a schema that already has them.
        """
        head = _mssql_script_directory().get_heads()[0]
        for name, storage in storages.items():
            assert storage.alembic_version() == (head, head), (
                f"{name} storage is not stamped at head"
            )

    @pytest.mark.parametrize("name", ["run", "event_log", "schedule"])
    def test_create_all_produced_every_table(self, storages, name):
        storage = storages[name]
        expected = {t.name for t in METADATA_BY_STORAGE[name].sorted_tables}
        with _connect(storage)() as conn:
            actual = set(db.inspect(conn).get_table_names())
        assert expected <= actual, f"tables missing from the database: {expected - actual}"

    @pytest.mark.parametrize("name", ["run", "event_log", "schedule"])
    def test_create_all_produced_every_column(self, storages, name):
        storage = storages[name]
        missing = []
        with _connect(storage)() as conn:
            inspector = db.inspect(conn)
            for table in METADATA_BY_STORAGE[name].sorted_tables:
                actual = {c["name"] for c in inspector.get_columns(table.name)}
                missing.extend(
                    f"{table.name}.{column.name}"
                    for column in table.columns
                    if column.name not in actual
                )
        assert not missing, f"columns missing from the database: {missing}"

    @pytest.mark.parametrize("name", ["run", "event_log", "schedule"])
    def test_create_all_produced_every_index(self, storages, name):
        """Every declared index has to actually exist.

        Worth asserting separately from the columns: SQL Server rejects an index whose key
        is unbounded or over 1700 bytes, and a schema that is otherwise complete but
        missing indexes degrades into table scans rather than failing.
        """
        storage = storages[name]
        missing = []
        with _connect(storage)() as conn:
            inspector = db.inspect(conn)
            for table in METADATA_BY_STORAGE[name].sorted_tables:
                actual = {i["name"] for i in inspector.get_indexes(table.name)}
                missing.extend(
                    f"{table.name}.{index.name}"
                    for index in table.indexes
                    if index.name not in actual
                )
        assert not missing, f"indexes missing from the database: {missing}"


class TestUpgradeIsSafe:
    def test_upgrade_on_a_fresh_database_is_a_no_op(self, conn_string):
        """`dagster instance migrate` against a just-created schema must change nothing.

        A fresh database is stamped at head, so every revision is already applied. If
        upgrade() were to replay any of them it would fail here rather than in the field.
        """
        TestMSSQLInstance.clean_run_storage(conn_string)
        storage = MSSQLRunStorage.create_clean_storage(conn_string)

        def snapshot():
            with _connect(storage)() as conn:
                inspector = db.inspect(conn)
                return {
                    table: (
                        sorted(c["name"] for c in inspector.get_columns(table)),
                        sorted(i["name"] for i in inspector.get_indexes(table)),
                    )
                    for table in sorted(inspector.get_table_names())
                }

        before = snapshot()
        storage.upgrade()
        storage.upgrade()  # twice: migrations have to be idempotent, not just survivable
        assert snapshot() == before
