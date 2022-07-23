# pylint: disable=protected-access

import os
import subprocess
import tempfile

from sqlalchemy import create_engine, inspect

from dagster import AssetKey, AssetObservation, Output, job, op
from dagster._utils import file_relative_path
from dagster.core.instance import DagsterInstance
from dagster.core.storage.event_log.migration import ASSET_KEY_INDEX_COLS


def get_columns(instance, table_name: str):
    return set(c["name"] for c in inspect(instance.run_storage._engine).get_columns(table_name))


def get_indexes(instance, table_name: str):
    return set(c["name"] for c in inspect(instance.run_storage._engine).get_indexes(table_name))


def get_tables(instance):
    return instance.run_storage._engine.table_names()


def _reconstruct_from_file(hostname, conn_string, path, _username="root", _password="test"):
    engine = create_engine(conn_string)
    engine.execute("drop schema test;")
    engine.execute("create schema test;")
    env = os.environ.copy()
    env["MYSQL_PWD"] = "test"
    subprocess.check_call(f"mysql -uroot -h{hostname} test < {path}", shell=True, env=env)


def test_0_13_17_mysql_convert_float_cols(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_13_18_start_end_timestamp.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(
            file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8"
        ) as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)
        record = instance.get_run_records(limit=1)[0]
        assert int(record.start_time) == 1643760000
        assert int(record.end_time) == 1643760000

        instance.upgrade()

        record = instance.get_run_records(limit=1)[0]
        assert record.start_time is None
        assert record.end_time is None

        instance.reindex()

        record = instance.get_run_records(limit=1)[0]
        assert int(record.start_time) == 1643788829
        assert int(record.end_time) == 1643788834


def test_instigators_table_backcompat(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_14_6_instigators_table.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(
            file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8"
        ) as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        assert not instance.schedule_storage.has_instigators_table()

        instance.upgrade()

        assert instance.schedule_storage.has_instigators_table()


def test_asset_observation_backcompat(hostname, conn_string):
    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_11_16_pre_add_asset_key_index_cols.sql"),
    )

    @op
    def asset_op(_):
        yield AssetObservation(asset_key=AssetKey(["a"]))
        yield Output(1)

    @job
    def asset_job():
        asset_op()

    with tempfile.TemporaryDirectory() as tempdir:
        with open(
            file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8"
        ) as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            storage = instance._event_storage

            assert not instance.event_log_storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            asset_job.execute_in_process(instance=instance)
            assert storage.has_asset_key(AssetKey(["a"]))


def test_jobs_selector_id_migration(hostname, conn_string):
    import sqlalchemy as db

    from dagster.core.storage.schedules.migration import SCHEDULE_JOBS_SELECTOR_ID
    from dagster.core.storage.schedules.schema import InstigatorsTable, JobTable, JobTickTable

    _reconstruct_from_file(
        hostname,
        conn_string,
        file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(
            file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8"
        ) as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
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


def test_add_bulk_actions_columns(hostname, conn_string):
    new_columns = {"selector_id", "action_type"}
    new_indexes = {"idx_bulk_actions_action_type", "idx_bulk_actions_selector_id"}

    _reconstruct_from_file(
        hostname,
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(
            file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8"
        ) as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:

            assert get_columns(instance, "bulk_actions") & new_columns == set()
            assert get_indexes(instance, "bulk_actions") & new_indexes == set()

            instance.upgrade()
            assert new_columns <= get_columns(instance, "bulk_actions")
            assert new_indexes <= get_indexes(instance, "bulk_actions")


def test_add_kvs_table(hostname, conn_string):

    _reconstruct_from_file(
        hostname,
        conn_string,
        # use an old snapshot
        file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(
            file_relative_path(__file__, "dagster.yaml"), "r", encoding="utf8"
        ) as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:

            assert "kvs" not in get_tables(instance)

            instance.upgrade()
            assert "kvs" in get_tables(instance)
            assert "idx_kvs_keys_unique" in get_indexes(instance, "kvs")
