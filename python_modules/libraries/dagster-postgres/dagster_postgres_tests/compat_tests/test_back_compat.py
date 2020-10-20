# pylint: disable=protected-access

import os
import re
import subprocess

import pytest
from dagster import execute_pipeline, pipeline, seven, solid
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance
from dagster.core.storage.event_log.migration import migrate_event_log_data
from dagster.core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster.utils import file_relative_path
from sqlalchemy import create_engine


def test_0_6_6_postgres(hostname, conn_string):
    # Init a fresh postgres with a 0.6.6 snapshot
    engine = create_engine(conn_string)
    engine.execute("drop schema public cascade;")
    engine.execute("create schema public;")

    env = os.environ.copy()
    env["PGPASSWORD"] = "test"
    subprocess.check_call(
        [
            "psql",
            "-h",
            hostname,
            "-p",
            "5432",
            "-U",
            "test",
            "-f",
            file_relative_path(__file__, "snapshot_0_6_6/postgres/pg_dump.txt"),
        ],
        env=env,
    )

    run_id = "089287c5-964d-44c0-b727-357eb7ba522e"

    with seven.TemporaryDirectory() as tempdir:
        # Create the dagster.yaml
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        # Runs will appear in DB, but event logs need migration
        runs = instance.get_runs()
        assert len(runs) == 1
        assert instance.get_run_by_id(run_id)

        assert instance.all_logs(run_id) == []

        # Post migration, event logs appear in DB
        instance.upgrade()

        runs = instance.get_runs()
        assert len(runs) == 1
        assert instance.get_run_by_id(run_id)

        assert len(instance.all_logs(run_id)) == 89


def test_0_7_6_postgres_pre_event_log_migration(hostname, conn_string):
    engine = create_engine(conn_string)
    engine.execute("drop schema public cascade;")
    engine.execute("create schema public;")

    env = os.environ.copy()
    env["PGPASSWORD"] = "test"
    subprocess.check_call(
        [
            "psql",
            "-h",
            hostname,
            "-p",
            "5432",
            "-U",
            "test",
            "-f",
            file_relative_path(
                __file__, "snapshot_0_7_6_pre_event_log_migration/postgres/pg_dump.txt"
            ),
        ],
        env=env,
    )

    run_id = "ca7f1e33-526d-4f75-9bc5-3e98da41ab97"

    with seven.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        # Runs will appear in DB, but event logs need migration
        runs = instance.get_runs()
        assert len(runs) == 1
        assert instance.get_run_by_id(run_id)

        # Make sure the schema is migrated
        instance.upgrade()

        assert isinstance(instance._event_storage, SqlEventLogStorage)
        events_by_id = instance._event_storage.get_logs_for_run_by_log_id(run_id)
        assert len(events_by_id) == 40

        step_key_records = []
        for record_id, _event in events_by_id.items():
            row_data = instance._event_storage.get_event_log_table_data(run_id, record_id)
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) == 0

        # run the event_log data migration
        migrate_event_log_data(instance=instance)

        step_key_records = []
        for record_id, _event in events_by_id.items():
            row_data = instance._event_storage.get_event_log_table_data(run_id, record_id)
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) > 0


def test_0_7_6_postgres_pre_add_pipeline_snapshot(hostname, conn_string):
    engine = create_engine(conn_string)
    engine.execute("drop schema public cascade;")
    engine.execute("create schema public;")

    env = os.environ.copy()
    env["PGPASSWORD"] = "test"
    subprocess.check_call(
        [
            "psql",
            "-h",
            hostname,
            "-p",
            "5432",
            "-U",
            "test",
            "-f",
            file_relative_path(
                __file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/postgres/pg_dump.txt"
            ),
        ],
        env=env,
    )

    run_id = "d5f89349-7477-4fab-913e-0925cef0a959"

    with seven.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        @solid
        def noop_solid(_):
            pass

        @pipeline
        def noop_pipeline():
            noop_solid()

        with pytest.raises(
            DagsterInstanceMigrationRequired, match=_migration_regex("run", current_revision=None)
        ):
            execute_pipeline(noop_pipeline, instance=instance)

        # ensure migration is run
        instance.upgrade()

        runs = instance.get_runs()

        assert len(runs) == 1

        assert runs[0].run_id == run_id

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


def _migration_regex(storage_name, current_revision, expected_revision=None):
    warning = re.escape(
        "Instance is out of date and must be migrated (Postgres {} storage requires migration).".format(
            storage_name
        )
    )
    if expected_revision:
        revision = re.escape(
            "Database is at revision {}, head is {}.".format(current_revision, expected_revision)
        )
    else:
        revision = "Database is at revision {}, head is [a-z0-9]+.".format(current_revision)
    instruction = re.escape("Please run `dagster instance migrate`.")

    return "{} {} {}".format(warning, revision, instruction)


def test_0_8_0_scheduler_update(hostname, conn_string):
    engine = create_engine(conn_string)
    engine.execute("drop schema public cascade;")
    engine.execute("create schema public;")

    env = os.environ.copy()
    env["PGPASSWORD"] = "test"
    subprocess.check_call(
        [
            "psql",
            "-h",
            hostname,
            "-p",
            "5432",
            "-U",
            "test",
            "-f",
            file_relative_path(__file__, "snapshot_0_8_0_scheduler_update/postgres/pg_dump.txt"),
        ],
        env=env,
    )

    with seven.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_migration_regex("schedule", current_revision=None),
        ):
            instance.all_stored_schedule_state()

        instance.upgrade()

        instance = DagsterInstance.from_config(tempdir)
        instance.all_stored_schedule_state()
