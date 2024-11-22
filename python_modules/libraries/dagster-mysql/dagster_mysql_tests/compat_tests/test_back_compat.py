# ruff: noqa: SLF001
import datetime
import os
import subprocess
import tempfile
from urllib.parse import urlparse

import pytest
import sqlalchemy as db
from dagster import AssetKey, AssetMaterialization, AssetObservation, Output, job, op
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus, PartitionBackfill
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external_data import partition_set_snap_name_for_job_name
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.event_log.migration import ASSET_KEY_INDEX_COLS
from dagster._core.storage.migration.bigint_migration import run_bigint_migration
from dagster._core.storage.runs.migration import BACKFILL_JOB_NAME_AND_TAGS, RUN_BACKFILL_ID
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.utils import make_new_run_id
from dagster._daemon.types import DaemonHeartbeat
from dagster._time import get_current_timestamp
from dagster._utils import file_relative_path


def get_columns(instance, table_name: str):
    with instance.run_storage.connect() as conn:
        return set(c["name"] for c in db.inspect(conn).get_columns(table_name))


def get_indexes(instance, table_name: str):
    with instance.run_storage.connect() as conn:
        return set(i["name"] for i in db.inspect(conn).get_indexes(table_name))


def get_tables(instance):
    with instance.run_storage.connect() as conn:
        return db.inspect(conn).get_table_names()


def _reconstruct_from_file(conn_string, path, _username="root", _password="test"):
    parse_result = urlparse(conn_string)
    hostname = parse_result.hostname
    port = parse_result.port
    engine = db.create_engine(conn_string)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(db.text("drop schema test;"))
            conn.execute(db.text("create schema test;"))
    env = os.environ.copy()
    env["MYSQL_PWD"] = "test"
    subprocess.check_call(
        f"mysql -uroot -h{hostname} -P{port} -ptest test < {path}", shell=True, env=env
    )
    return hostname, port


def test_0_13_17_mysql_convert_float_cols(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(__file__, "snapshot_0_13_18_start_end_timestamp.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
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


def test_instigators_table_backcompat(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(__file__, "snapshot_0_14_6_instigators_table.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        instance = DagsterInstance.from_config(tempdir)

        assert not instance.schedule_storage.has_instigators_table()

        instance.upgrade()

        assert instance.schedule_storage.has_instigators_table()


def test_asset_observation_backcompat(conn_string):
    hostname, port = _reconstruct_from_file(
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
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            storage = instance._event_storage

            assert not instance.event_log_storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            asset_job.execute_in_process(instance=instance)
            assert storage.has_asset_key(AssetKey(["a"]))


def test_jobs_selector_id_migration(conn_string):
    import sqlalchemy as db
    from dagster._core.storage.schedules.migration import SCHEDULE_JOBS_SELECTOR_ID
    from dagster._core.storage.schedules.schema import InstigatorsTable, JobTable, JobTickTable

    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            # runs the required data migrations
            instance.upgrade()

            assert instance.schedule_storage.has_built_index(SCHEDULE_JOBS_SELECTOR_ID)
            legacy_count = len(instance.all_instigator_state())
            migrated_instigator_count = instance.schedule_storage.execute(
                db_select([db.func.count()]).select_from(InstigatorsTable)
            )[0][0]
            assert migrated_instigator_count == legacy_count

            migrated_job_count = instance.schedule_storage.execute(
                db_select([db.func.count()])
                .select_from(JobTable)
                .where(JobTable.c.selector_id.isnot(None))
            )[0][0]
            assert migrated_job_count == legacy_count

            legacy_tick_count = instance.schedule_storage.execute(
                db_select([db.func.count()]).select_from(JobTickTable)
            )[0][0]
            assert legacy_tick_count > 0

            # tick migrations are optional
            migrated_tick_count = instance.schedule_storage.execute(
                db_select([db.func.count()])
                .select_from(JobTickTable)
                .where(JobTickTable.c.selector_id.isnot(None))
            )[0][0]
            assert migrated_tick_count == 0

            # run the optional migrations
            instance.reindex()

            migrated_tick_count = instance.schedule_storage.execute(
                db_select([db.func.count()])
                .select_from(JobTickTable)
                .where(JobTickTable.c.selector_id.isnot(None))
            )[0][0]
            assert migrated_tick_count == legacy_tick_count


def test_add_bulk_actions_columns(conn_string):
    new_columns = {"selector_id", "action_type"}
    new_indexes = {"idx_bulk_actions_action_type", "idx_bulk_actions_selector_id"}

    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert get_columns(instance, "bulk_actions") & new_columns == set()
            assert get_indexes(instance, "bulk_actions") & new_indexes == set()

            instance.upgrade()
            assert new_columns <= get_columns(instance, "bulk_actions")
            assert new_indexes <= get_indexes(instance, "bulk_actions")


def test_add_kvs_table(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot
        file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert "kvs" not in get_tables(instance)

            instance.upgrade()
            assert "kvs" in get_tables(instance)
            assert "idx_kvs_keys_unique" in get_indexes(instance, "kvs")


def test_add_asset_event_tags_table(conn_string):
    @op
    def yields_materialization_w_tags(_):
        yield AssetMaterialization(asset_key=AssetKey(["a"]), tags={DATA_VERSION_TAG: "bar"})
        yield Output(1)

    @job
    def asset_job():
        yields_materialization_w_tags()

    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot
        file_relative_path(__file__, "snapshot_1_0_12_pre_add_asset_event_tags_table.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert "asset_event_tags" not in get_tables(instance)
            asset_job.execute_in_process(instance=instance)
            with pytest.raises(
                DagsterInvalidInvocationError, match="In order to search for asset event tags"
            ):
                instance._event_storage.get_event_tags_for_asset(asset_key=AssetKey(["a"]))

            instance.upgrade()
            assert "asset_event_tags" in get_tables(instance)
            asset_job.execute_in_process(instance=instance)
            assert instance._event_storage.get_event_tags_for_asset(asset_key=AssetKey(["a"])) == [
                {DATA_VERSION_TAG: "bar"}
            ]

            indexes = get_indexes(instance, "asset_event_tags")
            assert "idx_asset_event_tags" in indexes
            assert "idx_asset_event_tags_event_id" in indexes


def test_add_cached_status_data_column(conn_string):
    new_columns = {"cached_status_data"}

    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(__file__, "snapshot_1_0_17_add_cached_status_data_column.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert get_columns(instance, "asset_keys") & new_columns == set()

            instance.upgrade()
            assert new_columns <= get_columns(instance, "asset_keys")


def test_add_dynamic_partitions_table(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(__file__, "snapshot_1_0_17_add_cached_status_data_column.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert "dynamic_partitions" not in get_tables(instance)

            instance.wipe()

            with pytest.raises(DagsterInvalidInvocationError, match="does not exist"):
                instance.get_dynamic_partitions("foo")

            instance.upgrade()
            assert "dynamic_partitions" in get_tables(instance)
            assert instance.get_dynamic_partitions("foo") == []


def _get_table_row_count(run_storage, table, with_non_null_id=False):
    import sqlalchemy as db

    query = db_select([db.func.count()]).select_from(table)
    if with_non_null_id:
        query = query.where(table.c.id.isnot(None))
    with run_storage.connect() as conn:
        row_count = conn.execute(query).fetchone()[0]
    return row_count


def test_add_primary_keys(conn_string):
    from dagster._core.storage.runs.schema import (
        DaemonHeartbeatsTable,
        InstanceInfo,
        KeyValueStoreTable,
    )

    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(__file__, "snapshot_1_1_22_pre_primary_key.sql"),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert "id" not in get_columns(instance, "kvs")
            # trigger insert, and update
            instance.run_storage.set_cursor_values({"a": "A"})
            instance.run_storage.set_cursor_values({"a": "A"})

            kvs_row_count = _get_table_row_count(instance.run_storage, KeyValueStoreTable)
            assert kvs_row_count > 0

            assert "id" not in get_columns(instance, "instance_info")
            instance_info_row_count = _get_table_row_count(instance.run_storage, InstanceInfo)
            assert instance_info_row_count > 0

            assert "id" not in get_columns(instance, "daemon_heartbeats")
            heartbeat = DaemonHeartbeat(
                timestamp=datetime.datetime.now().timestamp(), daemon_type="test", daemon_id="test"
            )
            instance.run_storage.add_daemon_heartbeat(heartbeat)
            instance.run_storage.add_daemon_heartbeat(heartbeat)
            daemon_heartbeats_row_count = _get_table_row_count(
                instance.run_storage, DaemonHeartbeatsTable
            )
            assert daemon_heartbeats_row_count > 0

            instance.upgrade()

            assert "id" in get_columns(instance, "kvs")
            with instance.run_storage.connect():
                kvs_id_count = _get_table_row_count(
                    instance.run_storage, KeyValueStoreTable, with_non_null_id=True
                )
            assert kvs_id_count == kvs_row_count

            assert "id" in get_columns(instance, "instance_info")
            with instance.run_storage.connect():
                instance_info_id_count = _get_table_row_count(
                    instance.run_storage, InstanceInfo, with_non_null_id=True
                )
            assert instance_info_id_count == instance_info_row_count

            assert "id" in get_columns(instance, "daemon_heartbeats")
            with instance.run_storage.connect():
                daemon_heartbeats_id_count = _get_table_row_count(
                    instance.run_storage, DaemonHeartbeatsTable, with_non_null_id=True
                )
            assert daemon_heartbeats_id_count == daemon_heartbeats_row_count


def test_bigint_migration(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(__file__, "snapshot_1_1_22_pre_primary_key.sql"),
    )

    def _get_integer_id_tables(conn):
        inspector = db.inspect(conn)
        integer_tables = set()
        for table in inspector.get_table_names():
            type_by_col_name = {c["name"]: c["type"] for c in db.inspect(conn).get_columns(table)}
            id_type = type_by_col_name.get("id")
            if id_type and str(id_type) == "INTEGER":
                integer_tables.add(table)
        return integer_tables

    def _assert_autoincrement_id(conn):
        inspector = db.inspect(conn)
        for table in inspector.get_table_names():
            id_cols = [col for col in inspector.get_columns(table) if col["name"] == "id"]
            if id_cols:
                id_col = id_cols[0]
                assert id_col["autoincrement"]

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            with instance.run_storage.connect() as conn:
                assert len(_get_integer_id_tables(conn)) > 0
                _assert_autoincrement_id(conn)
            with instance.event_log_storage.index_connection() as conn:
                assert len(_get_integer_id_tables(conn)) > 0
                _assert_autoincrement_id(conn)
            with instance.schedule_storage.connect() as conn:
                assert len(_get_integer_id_tables(conn)) > 0
                _assert_autoincrement_id(conn)

            run_bigint_migration(instance)

            with instance.run_storage.connect() as conn:
                assert len(_get_integer_id_tables(conn)) == 0
                _assert_autoincrement_id(conn)
            with instance.event_log_storage.index_connection() as conn:
                assert len(_get_integer_id_tables(conn)) == 0
                _assert_autoincrement_id(conn)
            with instance.schedule_storage.connect() as conn:
                assert len(_get_integer_id_tables(conn)) == 0
                _assert_autoincrement_id(conn)


def test_add_backfill_id_column(conn_string):
    from dagster._core.storage.runs.schema import RunsTable

    new_columns = {"backfill_id"}

    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(
            __file__, "snapshot_1_8_12_pre_add_backfill_id_column_to_runs_table.sql"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert get_columns(instance, "runs") & new_columns == set()

            # these runs won't have an entry for backfill_id until after the data migration
            run_not_in_backfill_pre_migration = instance.run_storage.add_run(
                DagsterRun(
                    job_name="first_job_no_backfill",
                    run_id=make_new_run_id(),
                    tags=None,
                    status=DagsterRunStatus.NOT_STARTED,
                )
            )
            run_in_backfill_pre_migration = instance.run_storage.add_run(
                DagsterRun(
                    job_name="first_job_in_backfill",
                    run_id=make_new_run_id(),
                    tags={BACKFILL_ID_TAG: "backfillid"},
                    status=DagsterRunStatus.NOT_STARTED,
                )
            )

            # exclude_subruns filter works before migration
            assert len(instance.get_runs(filters=RunsFilter(exclude_subruns=True))) == 2

            instance.upgrade()
            assert instance.run_storage.has_built_index(RUN_BACKFILL_ID)
            assert new_columns <= get_columns(instance, "runs")

            run_not_in_backfill_post_migration = instance.run_storage.add_run(
                DagsterRun(
                    job_name="second_job_no_backfill",
                    run_id=make_new_run_id(),
                    tags=None,
                    status=DagsterRunStatus.NOT_STARTED,
                )
            )
            run_in_backfill_post_migration = instance.run_storage.add_run(
                DagsterRun(
                    job_name="second_job_in_backfill",
                    run_id=make_new_run_id(),
                    tags={BACKFILL_ID_TAG: "backfillid"},
                    status=DagsterRunStatus.NOT_STARTED,
                )
            )

            backfill_ids = {
                row["run_id"]: row["backfill_id"]
                for row in instance._run_storage.fetchall(
                    db_select([RunsTable.c.run_id, RunsTable.c.backfill_id]).select_from(RunsTable)
                )
            }
            assert backfill_ids[run_not_in_backfill_pre_migration.run_id] is None
            assert backfill_ids[run_in_backfill_pre_migration.run_id] == "backfillid"
            assert backfill_ids[run_not_in_backfill_post_migration.run_id] is None
            assert backfill_ids[run_in_backfill_post_migration.run_id] == "backfillid"
            # exclude_subruns filter works after migration, but should use new column
            assert len(instance.get_runs(filters=RunsFilter(exclude_subruns=True))) == 3


def test_add_runs_by_backfill_id_idx(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        file_relative_path(
            __file__, "snapshot_1_8_12_pre_add_backfill_id_column_to_runs_table.sql"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert get_indexes(instance, "runs") & {"idx_runs_by_backfill_id"} == set()
            instance.upgrade()
            assert {"idx_runs_by_backfill_id"} <= get_indexes(instance, "runs")


def test_add_backfill_tags(conn_string):
    from dagster._core.storage.runs.schema import BackfillTagsTable

    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(
            __file__, "snapshot_1_8_12_pre_add_backfill_id_column_to_runs_table.sql"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert "backfill_tags" not in get_tables(instance)
            before_migration = PartitionBackfill(
                "before_tag_migration",
                serialized_asset_backfill_data="foo",
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={"before": "migration"},
                backfill_timestamp=get_current_timestamp(),
            )
            instance.add_backfill(before_migration)
            # filtering pre-migration relies on filtering runs, so add a run with the expected tags
            pre_migration_run = instance.run_storage.add_run(
                DagsterRun(
                    job_name="foo",
                    run_id=make_new_run_id(),
                    tags={"before": "migration", BACKFILL_ID_TAG: before_migration.backfill_id},
                    status=DagsterRunStatus.NOT_STARTED,
                )
            )

            # filtering by tags works before migration
            assert (
                instance.get_backfills(filters=BulkActionsFilter(tags={"before": "migration"}))[
                    0
                ].backfill_id
                == before_migration.backfill_id
            )

            instance.upgrade()
            assert "backfill_tags" in get_tables(instance)

            after_migration = PartitionBackfill(
                "after_tag_migration",
                serialized_asset_backfill_data="foo",
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={"after": "migration"},
                backfill_timestamp=get_current_timestamp(),
            )
            instance.add_backfill(after_migration)

            with instance.run_storage.connect() as conn:
                rows = conn.execute(
                    db_select(
                        [
                            BackfillTagsTable.c.backfill_id,
                            BackfillTagsTable.c.key,
                            BackfillTagsTable.c.value,
                        ]
                    )
                ).fetchall()
                assert len(rows) == 2
                ids_to_tags = {row[0]: {row[1]: row[2]} for row in rows}
                assert ids_to_tags.get(before_migration.backfill_id) == before_migration.tags
                assert ids_to_tags[after_migration.backfill_id] == after_migration.tags

                # filtering by tags works after migration
                assert instance.run_storage.has_built_index(BACKFILL_JOB_NAME_AND_TAGS)
                # delete the run that was added pre-migration to prove that tags filtering is happening on the
                # backfill_tags table
                instance.delete_run(pre_migration_run.run_id)
                assert (
                    instance.get_backfills(filters=BulkActionsFilter(tags={"before": "migration"}))[
                        0
                    ].backfill_id
                    == before_migration.backfill_id
                )
                assert (
                    instance.get_backfills(filters=BulkActionsFilter(tags={"after": "migration"}))[
                        0
                    ].backfill_id
                    == after_migration.backfill_id
                )


def test_add_bulk_actions_job_name_column(conn_string):
    from dagster._core.remote_representation.origin import (
        GrpcServerCodeLocationOrigin,
        RemotePartitionSetOrigin,
        RemoteRepositoryOrigin,
    )
    from dagster._core.storage.runs.schema import BulkActionsTable

    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(
            __file__, "snapshot_1_8_12_pre_add_backfill_id_column_to_runs_table.sql"
        ),
    )
    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            assert "job_name" not in get_columns(instance, "bulk_actions")
            partition_set_origin = RemotePartitionSetOrigin(
                repository_origin=RemoteRepositoryOrigin(
                    code_location_origin=GrpcServerCodeLocationOrigin(
                        host="localhost", port=1234, location_name="test_location"
                    ),
                    repository_name="the_repo",
                ),
                partition_set_name=partition_set_snap_name_for_job_name("before_migration"),
            )
            before_migration = PartitionBackfill(
                "before_migration",
                partition_set_origin=partition_set_origin,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=get_current_timestamp(),
            )
            instance.add_backfill(before_migration)
            # filtering pre-migration relies on filtering runs, so add a run with the expected job_name
            pre_migration_run = instance.run_storage.add_run(
                DagsterRun(
                    job_name=before_migration.job_name,
                    run_id=make_new_run_id(),
                    tags={BACKFILL_ID_TAG: before_migration.backfill_id},
                    status=DagsterRunStatus.NOT_STARTED,
                )
            )

            # filtering by job_name works before migration
            assert (
                instance.get_backfills(
                    filters=BulkActionsFilter(job_name=before_migration.job_name)
                )[0].backfill_id
                == before_migration.backfill_id
            )

            instance.upgrade()

            assert "job_name" in get_columns(instance, "bulk_actions")

            partition_set_origin = RemotePartitionSetOrigin(
                repository_origin=RemoteRepositoryOrigin(
                    code_location_origin=GrpcServerCodeLocationOrigin(
                        host="localhost", port=1234, location_name="test_location"
                    ),
                    repository_name="the_repo",
                ),
                partition_set_name=partition_set_snap_name_for_job_name("after_migration"),
            )
            after_migration = PartitionBackfill(
                "after_migration",
                partition_set_origin=partition_set_origin,
                status=BulkActionStatus.REQUESTED,
                from_failure=False,
                tags={},
                backfill_timestamp=get_current_timestamp(),
            )
            instance.add_backfill(after_migration)

            with instance.run_storage.connect() as conn:
                rows = conn.execute(
                    db_select([BulkActionsTable.c.key, BulkActionsTable.c.job_name])
                ).fetchall()
                assert len(rows) == 2
                ids_to_job_name = {row[0]: row[1] for row in rows}
                assert ids_to_job_name[before_migration.backfill_id] == before_migration.job_name
                assert ids_to_job_name[after_migration.backfill_id] == after_migration.job_name

                # filtering by job_name works after migration
                assert instance.run_storage.has_built_index(BACKFILL_JOB_NAME_AND_TAGS)
                # delete the run that was added pre-migration to prove that tags filtering is happening on the
                # backfill_tags table
                instance.delete_run(pre_migration_run.run_id)
                assert (
                    instance.get_backfills(
                        filters=BulkActionsFilter(job_name=before_migration.job_name)
                    )[0].backfill_id
                    == before_migration.backfill_id
                )
                assert (
                    instance.get_backfills(
                        filters=BulkActionsFilter(job_name=after_migration.job_name)
                    )[0].backfill_id
                    == after_migration.backfill_id
                )


def test_add_run_tags_run_id_idx(conn_string):
    hostname, port = _reconstruct_from_file(
        conn_string,
        # use an old snapshot, it has the bulk actions table but not the new columns
        file_relative_path(
            __file__, "snapshot_1_8_12_pre_add_backfill_id_column_to_runs_table.sql"
        ),
    )

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
                template = template_fd.read().format(hostname=hostname, port=port)
                target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            # Before migration
            assert "run_tags" in get_tables(instance)
            assert "idx_run_tags" in get_indexes(instance, "run_tags")
            assert "idx_run_tags_run_id" not in get_indexes(instance, "run_tags")

            # After upgrade
            instance.upgrade()

            assert "run_tags" in get_tables(instance)
            assert "idx_run_tags" not in get_indexes(instance, "run_tags")
            assert "idx_run_tags_run_id" in get_indexes(instance, "run_tags")
