# pylint: disable=protected-access

import os
import re
import subprocess
import tempfile

import pytest
from dagster import AssetKey, AssetMaterialization, Output, execute_pipeline, pipeline, solid
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.core.instance import DagsterInstance
from dagster.core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster.utils import file_relative_path
from sqlalchemy import create_engine


def test_0_7_6_postgres_pre_add_pipeline_snapshot(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(
            __file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/postgres/pg_dump.txt"
        ),
    )

    run_id = "d5f89349-7477-4fab-913e-0925cef0a959"

    with tempfile.TemporaryDirectory() as tempdir:
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


def test_0_9_22_postgres_pre_asset_partition(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_9_22_pre_asset_partition/postgres/pg_dump.txt"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        @solid
        def asset_solid(_):
            yield AssetMaterialization(
                asset_key=AssetKey(["path", "to", "asset"]), partition="partition_1"
            )
            yield Output(1)

        @pipeline
        def asset_pipeline():
            asset_solid()

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_migration_regex("run", current_revision="c9159e740d7e"),
        ):
            execute_pipeline(asset_pipeline, instance=instance)

        # ensure migration is run
        instance.upgrade()

        result = execute_pipeline(asset_pipeline, instance=instance)
        assert result.success


def test_0_9_22_postgres_pre_run_partition(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_9_22_pre_run_partition/postgres/pg_dump.txt"),
    )
    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        @solid
        def simple_solid(_):
            return 1

        @pipeline
        def simple_pipeline():
            simple_solid()

        tags = {PARTITION_NAME_TAG: "my_partition", PARTITION_SET_TAG: "my_partition_set"}

        with pytest.raises(
            DagsterInstanceMigrationRequired,
            match=_migration_regex("run", current_revision="3e0770016702"),
        ):
            execute_pipeline(simple_pipeline, tags=tags, instance=instance)

        # ensure migration is run
        instance.upgrade()

        result = execute_pipeline(simple_pipeline, tags=tags, instance=instance)
        assert result.success


def test_0_10_0_schedule_wipe(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_10_0_wipe_schedules/postgres/pg_dump.txt"),
    )
    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with pytest.raises(DagsterInstanceMigrationRequired):
            with DagsterInstance.from_config(tempdir) as instance:
                instance.optimize_for_dagit(statement_timeout=500)

        with DagsterInstance.from_config(tempdir) as instance:
            instance.upgrade()

        with DagsterInstance.from_config(tempdir) as upgraded_instance:
            assert len(upgraded_instance.all_stored_job_state()) == 0


def test_0_10_6_add_bulk_actions_table(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_10_6_add_bulk_actions_table/postgres/pg_dump.txt"),
    )
    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with pytest.raises(DagsterInstanceMigrationRequired):
            with DagsterInstance.from_config(tempdir) as instance:
                instance.get_backfills()

        with DagsterInstance.from_config(tempdir) as instance:
            instance.upgrade()

        with DagsterInstance.from_config(tempdir) as upgraded_instance:
            assert len(upgraded_instance.get_backfills()) == 0


def test_0_11_0_add_asset_details(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_11_0_pre_asset_details/postgres/pg_dump.txt"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            storage = instance._event_storage
            with pytest.raises(
                DagsterInstanceMigrationRequired,
                match=_migration_regex("event log", current_revision="3e71cf573ba6"),
            ):
                storage.get_asset_tags(AssetKey(["test"]))
                storage.all_asset_keys()
            instance.upgrade()
            storage.get_asset_tags(AssetKey(["test"]))
            storage.all_asset_keys()


def _reconstruct_from_file(hostname, conn_string, path, username="test", password="test"):
    engine = create_engine(conn_string)
    engine.execute("drop schema public cascade;")
    engine.execute("create schema public;")
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    subprocess.check_call(
        ["psql", "-h", hostname, "-p", "5432", "-U", username, "-f", path],
        env=env,
    )


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
