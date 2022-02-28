# pylint: disable=protected-access

import os
import re
import subprocess
import tempfile

import pytest
from sqlalchemy import create_engine

from dagster import (
    AssetKey,
    AssetMaterialization,
    Output,
    execute_pipeline,
    job,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.errors import DagsterInstanceSchemaOutdated
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import RunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster.utils import file_relative_path


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
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
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
            DagsterInstanceSchemaOutdated, match=_migration_regex(current_revision=None)
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
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
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
            DagsterInstanceSchemaOutdated,
            match=_migration_regex(current_revision="c9159e740d7e"),
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
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
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
            DagsterInstanceSchemaOutdated,
            match=_migration_regex(current_revision="3e0770016702"),
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
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            instance.upgrade()

        with DagsterInstance.from_config(tempdir) as upgraded_instance:
            assert len(upgraded_instance.all_instigator_state()) == 0


def test_0_10_6_add_bulk_actions_table(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_10_6_add_bulk_actions_table/postgres/pg_dump.txt"),
    )
    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with pytest.raises(DagsterInstanceSchemaOutdated):
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
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            storage = instance._event_storage
            with pytest.raises(
                DagsterInstanceSchemaOutdated,
                match=_migration_regex(current_revision="3e71cf573ba6"),
            ):
                storage.all_asset_keys()
            instance.upgrade()
            storage.all_asset_keys()


def test_0_12_0_add_mode_column(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_11_16_pre_add_mode_column/postgres/pg_dump.txt"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        # Ensure that you don't get a migration required exception if not trying to use the
        # migration-required column.
        assert len(instance.get_runs()) == 1

        @solid
        def basic():
            pass

        @pipeline
        def noop_pipeline():
            basic()

        # Ensure that you don't get a migration required exception when running a pipeline
        # pre-migration.
        result = execute_pipeline(noop_pipeline, instance=instance)
        assert result.success
        assert len(instance.get_runs()) == 2

        # Ensure that migration required exception throws, since you are trying to use the
        # migration-required column.
        with pytest.raises(
            DagsterInstanceSchemaOutdated,
            match=_migration_regex(current_revision="7cba9eeaaf1d"),
        ):
            instance.get_runs(filters=RunsFilter(mode="the_mode"))

        instance.upgrade()

        result = execute_pipeline(noop_pipeline, instance=instance)
        assert result.success
        assert len(instance.get_runs()) == 3


def test_0_12_0_extract_asset_index_cols(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_12_0_pre_asset_index_cols/postgres/pg_dump.txt"),
    )

    @solid
    def asset_solid(_):
        yield AssetMaterialization(
            asset_key=AssetKey(["a"]), partition="partition_1", tags={"foo": "FOO"}
        )
        yield Output(1)

    @pipeline
    def asset_pipeline():
        asset_solid()

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            storage = instance._event_storage

            # make sure that executing the pipeline works
            execute_pipeline(asset_pipeline, instance=instance)
            assert storage.has_asset_key(AssetKey(["a"]))

            # make sure that wiping works
            storage.wipe_asset(AssetKey(["a"]))
            assert not storage.has_asset_key(AssetKey(["a"]))

            execute_pipeline(asset_pipeline, instance=instance)
            assert storage.has_asset_key(AssetKey(["a"]))
            old_keys = storage.all_asset_keys()

            instance.upgrade()
            assert storage.has_asset_key(AssetKey(["a"]))
            new_keys = storage.all_asset_keys()
            assert set(old_keys) == set(new_keys)

            # make sure that storing assets still works
            execute_pipeline(asset_pipeline, instance=instance)

            # make sure that wiping still works
            storage.wipe_asset(AssetKey(["a"]))
            assert not storage.has_asset_key(AssetKey(["a"]))


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


def _migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Raised an exception that may indicate that the Dagster database needs to be be migrated."
    )

    if expected_revision:
        revision = re.escape(
            "Database is at revision {}, head is {}.".format(current_revision, expected_revision)
        )
    else:
        revision = "Database is at revision {}, head is [a-z0-9]+.".format(current_revision)
    instruction = re.escape("To migrate, run `dagster instance migrate`.")

    return "{} {} {}".format(warning, revision, instruction)


def get_the_job():
    @job
    def the_job():
        pass

    return the_job


def test_0_13_12_add_start_time_end_time(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(
            __file__, "snapshot_0_13_12_pre_start_time_end_time/postgres/pg_dump.txt"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        # Ensure that you don't get a migration required exception if not trying to use the
        # migration-required column.
        assert len(instance.get_runs()) == 1

        # Ensure that you don't get a migration required exception when running a pipeline
        # pre-migration.
        result = execute_pipeline(reconstructable(get_the_job), instance=instance)
        assert result.success
        assert len(instance.get_runs()) == 2

        instance.upgrade()
        instance.reindex()

        result = execute_pipeline(reconstructable(get_the_job), instance=instance)
        assert result.success
        assert len(instance.get_runs()) == 3
        latest_run_record = instance.get_run_records()[0]
        assert latest_run_record.end_time > latest_run_record.start_time

        # Verify that historical records also get updated via data migration
        earliest_run_record = instance.get_run_records()[-1]
        assert earliest_run_record.end_time > earliest_run_record.start_time


def test_schedule_secondary_index_table_backcompat(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(
            __file__, "snapshot_0_14_6_schedule_migration_table/postgres/pg_dump.txt"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        # secondary indexes should exist because it's colocated in this database from the run
        # storage
        assert instance.schedule_storage.has_secondary_index_table()

        # this should succeed without raising any issues
        instance.upgrade()

        # no-op
        assert instance.schedule_storage.has_secondary_index_table()


def test_instigators_table_backcompat(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_14_6_instigators_table/postgres/pg_dump.txt"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        assert not instance.schedule_storage.has_instigators_table()

        instance.upgrade()

        assert instance.schedule_storage.has_instigators_table()


def test_jobs_selector_id_migration(hostname, conn_string):
    import sqlalchemy as db

    from dagster.core.storage.schedules.migration import SCHEDULE_JOBS_SELECTOR_ID
    from dagster.core.storage.schedules.schema import InstigatorsTable, JobTable, JobTickTable

    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(
            __file__, "snapshot_0_14_6_post_schema_pre_data_migration/postgres/pg_dump.txt"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), "r") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:

            # runs the required data migrations
            instance.upgrade()

            assert instance.schedule_storage.has_built_index(SCHEDULE_JOBS_SELECTOR_ID)
            legacy_count = len(instance.all_instigator_state())
            migrated_instigator_count = instance.schedule_storage.execute(
                db.select([db.func.count()]).select_from(InstigatorsTable)
            )[0][0]
            assert migrated_instigator_count == legacy_count

            migrated_job_count = instance.schedule_storage.execute(
                db.select([db.func.count()])
                .select_from(JobTable)
                .where(JobTable.c.selector_id.isnot(None))
            )[0][0]
            assert migrated_job_count == legacy_count

            legacy_tick_count = instance.schedule_storage.execute(
                db.select([db.func.count()]).select_from(JobTickTable)
            )[0][0]
            assert legacy_tick_count > 0

            # tick migrations are optional
            migrated_tick_count = instance.schedule_storage.execute(
                db.select([db.func.count()])
                .select_from(JobTickTable)
                .where(JobTickTable.c.selector_id.isnot(None))
            )[0][0]
            assert migrated_tick_count == 0

            # run the optional migrations
            instance.reindex()

            migrated_tick_count = instance.schedule_storage.execute(
                db.select([db.func.count()])
                .select_from(JobTickTable)
                .where(JobTickTable.c.selector_id.isnot(None))
            )[0][0]
            assert migrated_tick_count == legacy_tick_count
