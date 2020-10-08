# pylint: disable=protected-access
import os
import re
import sqlite3

import pytest

from dagster import execute_pipeline, file_relative_path, pipeline, solid
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.storage.event_log.migration import migrate_event_log_data
from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster.utils.test import restore_directory


def _migration_regex(warning, current_revision, expected_revision=None):
    instruction = re.escape("Please run `dagster instance migrate`.")
    if expected_revision:
        revision = re.escape(
            "Database is at revision {}, head is {}.".format(current_revision, expected_revision)
        )
    else:
        revision = "Database is at revision {}, head is [a-z0-9]+.".format(current_revision)
    return "{} {} {}".format(warning, revision, instruction)


def _run_storage_migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (Sqlite run storage requires migration)."
    )
    return _migration_regex(warning, current_revision, expected_revision)


def _schedule_storage_migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (Sqlite schedule storage requires migration)."
    )
    return _migration_regex(warning, current_revision, expected_revision)


def _event_log_migration_regex(run_id, current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (SqliteEventLogStorage for run {}).".format(
            run_id
        )
    )
    return _migration_regex(warning, current_revision, expected_revision)


# test that we can load runs and events from an old instance
def test_0_6_4():
    test_dir = file_relative_path(__file__, "snapshot_0_6_4")
    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        runs = instance.get_runs()
        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_event_log_migration_regex(
                run_id="c7a6c4d7-6c88-46d0-8baa-d4937c3cefe5", current_revision=None
            ),
        ):
            for run in runs:
                instance.all_logs(run.run_id)


def test_0_6_6_sqlite_exc():
    test_dir = file_relative_path(__file__, "snapshot_0_6_6/sqlite")
    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        runs = instance.get_runs()
        # Note that this is a deliberate choice -- old runs are simply invisible, and their
        # presence won't raise DagsterInstanceMigrationRequired. This is a reasonable choice since
        # the runs.db has moved and otherwise we would have to do a check for the existence of an
        # old runs.db every time we accessed the runs. Instead, we'll do this only in the upgrade
        # method.
        assert len(runs) == 0

        run_ids = instance._event_storage.get_all_run_ids()
        assert run_ids == ["89296095-892d-4a15-aa0d-9018d1580945"]

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_event_log_migration_regex(
                run_id="89296095-892d-4a15-aa0d-9018d1580945", current_revision=None
            ),
        ):
            instance._event_storage.get_logs_for_run("89296095-892d-4a15-aa0d-9018d1580945")


def test_0_6_6_sqlite_migrate():
    test_dir = file_relative_path(__file__, "snapshot_0_6_6/sqlite")
    assert os.path.exists(file_relative_path(__file__, "snapshot_0_6_6/sqlite/runs.db"))
    assert not os.path.exists(file_relative_path(__file__, "snapshot_0_6_6/sqlite/history/runs.db"))

    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        runs = instance.get_runs()
        assert len(runs) == 1

        run_ids = instance._event_storage.get_all_run_ids()
        assert run_ids == ["89296095-892d-4a15-aa0d-9018d1580945"]

        instance._event_storage.get_logs_for_run("89296095-892d-4a15-aa0d-9018d1580945")

        assert not os.path.exists(file_relative_path(__file__, "snapshot_0_6_6/sqlite/runs.db"))
        assert os.path.exists(file_relative_path(__file__, "snapshot_0_6_6/sqlite/history/runs.db"))


def test_event_log_step_key_migration():
    test_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_event_log_migration/sqlite")
    with restore_directory(test_dir):
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        # Make sure the schema is migrated
        instance.upgrade()

        runs = instance.get_runs()
        assert len(runs) == 1
        run_ids = instance._event_storage.get_all_run_ids()
        assert run_ids == ["6405c4a0-3ccc-4600-af81-b5ee197f8528"]
        assert isinstance(instance._event_storage, SqlEventLogStorage)
        events_by_id = instance._event_storage.get_logs_for_run_by_log_id(
            "6405c4a0-3ccc-4600-af81-b5ee197f8528"
        )
        assert len(events_by_id) == 40

        step_key_records = []
        for record_id, _event in events_by_id.items():
            row_data = instance._event_storage.get_event_log_table_data(
                "6405c4a0-3ccc-4600-af81-b5ee197f8528", record_id
            )
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) == 0

        # run the event_log backfill migration
        migrate_event_log_data(instance=instance)

        step_key_records = []
        for record_id, _event in events_by_id.items():
            row_data = instance._event_storage.get_event_log_table_data(
                "6405c4a0-3ccc-4600-af81-b5ee197f8528", record_id
            )
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) > 0


def get_sqlite3_tables(db_path):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [r[0] for r in cursor.fetchall()]


def get_current_alembic_version(db_path):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("SELECT * FROM alembic_version")
    return cursor.fetchall()[0][0]


def get_sqlite3_columns(db_path, table_name):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute('PRAGMA table_info("{}");'.format(table_name))
    return [r[1] for r in cursor.fetchall()]


def test_snapshot_0_7_6_pre_add_pipeline_snapshot():
    run_id = "fb0b3905-068b-4444-8f00-76fcbaef7e8b"
    test_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with restore_directory(test_dir):
        # invariant check to make sure migration has not been run yet

        db_path = os.path.join(test_dir, "history", "runs.db")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        @solid
        def noop_solid(_):
            pass

        @pipeline
        def noop_pipeline():
            noop_solid()

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_run_storage_migration_regex(current_revision="9fe9e746268c"),
        ):
            execute_pipeline(noop_pipeline, instance=instance)

        assert len(instance.get_runs()) == 1

        # Make sure the schema is migrated
        instance.upgrade()

        assert get_current_alembic_version(db_path) == "c63a27054f08"

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1

        run = instance.get_run_by_id(run_id)

        assert run.run_id == run_id
        assert run.pipeline_snapshot_id is None

        result = execute_pipeline(noop_pipeline, instance=instance)

        assert result.success

        runs = instance.get_runs()
        assert len(runs) == 2

        new_run_id = result.run_id

        new_run = instance.get_run_by_id(new_run_id)

        assert new_run.pipeline_snapshot_id


def test_downgrade_and_upgrade():
    test_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with restore_directory(test_dir):
        # invariant check to make sure migration has not been run yet

        db_path = os.path.join(test_dir, "history", "runs.db")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        assert len(instance.get_runs()) == 1

        # Make sure the schema is migrated
        instance.upgrade()

        assert get_current_alembic_version(db_path) == "c63a27054f08"

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1

        instance._run_storage._alembic_downgrade(rev="9fe9e746268c")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        assert len(instance.get_runs()) == 1

        instance.upgrade()

        assert get_current_alembic_version(db_path) == "c63a27054f08"

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1


def test_event_log_asset_key_migration():
    test_dir = file_relative_path(__file__, "snapshot_0_7_8_pre_asset_key_migration/sqlite")
    with restore_directory(test_dir):
        db_path = os.path.join(
            test_dir, "history", "runs", "722183e4-119f-4a00-853f-e1257be82ddb.db"
        )
        assert get_current_alembic_version(db_path) == "3b1e175a2be3"
        assert "asset_key" not in set(get_sqlite3_columns(db_path, "event_log"))

        # Make sure the schema is migrated
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        assert "asset_key" in set(get_sqlite3_columns(db_path, "event_logs"))


def test_0_8_0_scheduler_migration():
    test_dir = file_relative_path(__file__, "snapshot_0_8_0_scheduler_change")
    with restore_directory(test_dir):

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_schedule_storage_migration_regex(current_revision="da7cd32b690d"),
        ):
            instance.all_stored_schedule_state()

        instance.upgrade()

        # upgrade just drops tables, and user upgrade flow is cli entry - so
        # emulate by new-ing up instance which will create new tables
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        instance.all_stored_schedule_state()
