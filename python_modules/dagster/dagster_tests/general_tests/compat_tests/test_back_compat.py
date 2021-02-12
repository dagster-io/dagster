# pylint: disable=protected-access
import os
import re
import sqlite3
from gzip import GzipFile

import pytest
from dagster import check, execute_pipeline, file_relative_path, pipeline, solid
from dagster.cli.debug import DebugRunPayload
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.storage.event_log.migration import migrate_event_log_data
from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils.test import copy_directory


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


def test_event_log_step_key_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_event_log_migration/sqlite")
    with copy_directory(src_dir) as test_dir:
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
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with copy_directory(src_dir) as test_dir:
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
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with copy_directory(src_dir) as test_dir:
        # invariant check to make sure migration has not been run yet

        db_path = os.path.join(test_dir, "history", "runs.db")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        assert len(instance.get_runs()) == 1

        # Make sure the schema is migrated
        instance.upgrade()

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

        assert "snapshots" in get_sqlite3_tables(db_path)
        assert {"id", "snapshot_id", "snapshot_body", "snapshot_type"} == set(
            get_sqlite3_columns(db_path, "snapshots")
        )

        assert len(instance.get_runs()) == 1


def test_event_log_asset_key_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_7_8_pre_asset_key_migration/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(
            test_dir, "history", "runs", "722183e4-119f-4a00-853f-e1257be82ddb.db"
        )
        assert get_current_alembic_version(db_path) == "3b1e175a2be3"
        assert "asset_key" not in set(get_sqlite3_columns(db_path, "event_logs"))

        # Make sure the schema is migrated
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        assert "asset_key" in set(get_sqlite3_columns(db_path, "event_logs"))


def instance_from_debug_payloads(payload_files):
    debug_payloads = []
    for input_file in payload_files:
        with GzipFile(input_file, "rb") as file:
            blob = file.read().decode("utf-8")
            debug_payload = deserialize_json_to_dagster_namedtuple(blob)

            check.invariant(isinstance(debug_payload, DebugRunPayload))

            debug_payloads.append(debug_payload)

    return DagsterInstance.ephemeral(preload=debug_payloads)


def test_object_store_operation_result_data_new_fields():
    """We added address and version fields to ObjectStoreOperationResultData.
    Make sure we can still deserialize old ObjectStoreOperationResultData without those fields."""
    instance_from_debug_payloads([file_relative_path(__file__, "0_9_12_nothing_fs_storage.gz")])


def test_event_log_asset_partition_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_9_22_pre_asset_partition/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(
            test_dir, "history", "runs", "1a1d3c4b-1284-4c74-830c-c8988bd4d779.db"
        )
        assert get_current_alembic_version(db_path) == "c34498c29964"
        assert "partition" not in set(get_sqlite3_columns(db_path, "event_logs"))

        # Make sure the schema is migrated
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        assert "partition" in set(get_sqlite3_columns(db_path, "event_logs"))


def test_run_partition_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_9_22_pre_run_partition/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "224640159acf"
        assert "partition" not in set(get_sqlite3_columns(db_path, "runs"))
        assert "partition_set" not in set(get_sqlite3_columns(db_path, "runs"))

        # Make sure the schema is migrated
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        instance.upgrade()

        assert "partition" in set(get_sqlite3_columns(db_path, "runs"))
        assert "partition_set" in set(get_sqlite3_columns(db_path, "runs"))

        instance._run_storage._alembic_downgrade(rev="224640159acf")
        assert get_current_alembic_version(db_path) == "224640159acf"

        assert "partition" not in set(get_sqlite3_columns(db_path, "runs"))
        assert "partition_set" not in set(get_sqlite3_columns(db_path, "runs"))


def test_run_partition_data_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_9_22_post_schema_pre_data_partition/sqlite")
    with copy_directory(src_dir) as test_dir:
        from dagster.core.storage.runs.sql_run_storage import SqlRunStorage
        from dagster.core.storage.runs.migration import RUN_PARTITIONS

        # load db that has migrated schema, but not populated data for run partitions
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "375e95bad550"

        # Make sure the schema is migrated
        assert "partition" in set(get_sqlite3_columns(db_path, "runs"))
        assert "partition_set" in set(get_sqlite3_columns(db_path, "runs"))

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance._run_storage.upgrade()

        run_storage = instance._run_storage
        assert isinstance(run_storage, SqlRunStorage)

        partition_set_name = "ingest_and_train"
        partition_name = "2020-01-02"

        # ensure old tag-based reads are working
        assert not run_storage.has_built_index(RUN_PARTITIONS)
        assert len(run_storage._get_partition_runs(partition_set_name, partition_name)) == 2

        # turn on reads for the partition column, without migrating the data
        run_storage.mark_index_built(RUN_PARTITIONS)

        # ensure that no runs are returned because the data has not been migrated
        assert run_storage.has_built_index(RUN_PARTITIONS)
        assert len(run_storage._get_partition_runs(partition_set_name, partition_name)) == 0

        # actually migrate the data
        run_storage.build_missing_indexes(force_rebuild_all=True)

        # ensure that we get the same partitioned runs returned
        assert run_storage.has_built_index(RUN_PARTITIONS)
        assert len(run_storage._get_partition_runs(partition_set_name, partition_name)) == 2


def test_0_10_0_schedule_wipe():
    src_dir = file_relative_path(__file__, "snapshot_0_10_0_wipe_schedules/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "schedules", "schedules.db")

        assert get_current_alembic_version(db_path) == "b22f16781a7c"

        assert "schedules" in get_sqlite3_tables(db_path)
        assert "schedule_ticks" in get_sqlite3_tables(db_path)

        assert "jobs" not in get_sqlite3_tables(db_path)
        assert "job_ticks" not in get_sqlite3_tables(db_path)

        with pytest.raises(DagsterInstanceMigrationRequired):
            with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
                pass

        with DagsterInstance.from_ref(
            InstanceRef.from_dir(test_dir), skip_validation_checks=True
        ) as instance:
            instance.upgrade()

        assert "schedules" not in get_sqlite3_tables(db_path)
        assert "schedule_ticks" not in get_sqlite3_tables(db_path)

        assert "jobs" in get_sqlite3_tables(db_path)
        assert "job_ticks" in get_sqlite3_tables(db_path)

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as upgraded_instance:
            assert len(upgraded_instance.all_stored_job_state()) == 0


def test_0_10_6_add_bulk_actions_table():
    src_dir = file_relative_path(__file__, "snapshot_0_10_6_add_bulk_actions_table/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "0da417ae1b81"
        assert "bulk_actions" not in get_sqlite3_tables(db_path)
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert not instance.has_bulk_actions_table()
            instance.upgrade()
            assert instance.has_bulk_actions_table()
