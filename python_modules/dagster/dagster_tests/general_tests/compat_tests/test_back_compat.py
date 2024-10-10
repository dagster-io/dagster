# ruff: noqa: SLF001
import datetime
import json
import os
import re
import sqlite3
import time
from collections import namedtuple
from enum import Enum
from gzip import GzipFile
from typing import NamedTuple, Optional, Union

import pytest
import sqlalchemy as db
from dagster import (
    AssetKey,
    AssetMaterialization,
    Output,
    _check as check,
    asset,
    file_relative_path,
    job,
    op,
)
from dagster._cli.debug import DebugRunPayload
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.events import UNDEFINED_ASSET_KEY_PATH, AssetLineageInfo
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.events import DagsterEvent, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.remote_representation.external_data import StaticPartitionsSnap
from dagster._core.scheduler.instigation import InstigatorState, InstigatorTick
from dagster._core.snap.job_snapshot import JobSnap
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.event_log.migration import migrate_event_log_data
from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster._core.storage.migration.utils import upgrading_instance
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.storage.tags import (
    COMPUTE_KIND_TAG,
    LEGACY_COMPUTE_KIND_TAG,
    REPOSITORY_LABEL_TAG,
)
from dagster._daemon.types import DaemonHeartbeat
from dagster._serdes import create_snapshot_id
from dagster._serdes.serdes import (
    WhitelistMap,
    _whitelist_for_serdes,
    deserialize_value,
    pack_value,
    serialize_value,
)
from dagster._time import get_current_timestamp
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.test import copy_directory


def _migration_regex(warning, current_revision, expected_revision=None):
    instruction = re.escape("To migrate, run `dagster instance migrate`.")
    if expected_revision:
        revision = re.escape(
            f"Database is at revision {current_revision}, head is {expected_revision}."
        )
    else:
        revision = f"Database is at revision {current_revision}, head is [a-z0-9]+."
    return f"{warning} {revision} {instruction}"


def _run_storage_migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Raised an exception that may indicate that the Dagster database needs to be migrated."
    )
    return _migration_regex(warning, current_revision, expected_revision)


def _schedule_storage_migration_regex(current_revision, expected_revision=None):
    warning = re.escape(
        "Raised an exception that may indicate that the Dagster database needs to be migrated."
    )
    return _migration_regex(warning, current_revision, expected_revision)


def _event_log_migration_regex(_run_id, current_revision, expected_revision=None):
    warning = re.escape(
        "Raised an exception that may indicate that the Dagster database needs to be migrated."
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
        records = instance._event_storage.get_records_for_run(
            "6405c4a0-3ccc-4600-af81-b5ee197f8528"
        ).records
        assert len(records) == 40

        step_key_records = []
        for record in records:
            row_data = instance._event_storage.get_event_log_table_data(
                "6405c4a0-3ccc-4600-af81-b5ee197f8528", record.storage_id
            )
            if row_data.step_key is not None:
                step_key_records.append(row_data)
        assert len(step_key_records) == 0

        # run the event_log backfill migration
        migrate_event_log_data(instance=instance)

        step_key_records = []
        for record in records:
            row_data = instance._event_storage.get_event_log_table_data(
                "6405c4a0-3ccc-4600-af81-b5ee197f8528", record.storage_id
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
    cursor.execute(f'PRAGMA table_info("{table_name}");')
    return [r[1] for r in cursor.fetchall()]


def get_sqlite3_indexes(db_path, table_name):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute(f'PRAGMA index_list("{table_name}");')
    return [r[1] for r in cursor.fetchall()]


def test_snapshot_0_7_6_pre_add_job_snapshot():
    run_id = "fb0b3905-068b-4444-8f00-76fcbaef7e8b"
    src_dir = file_relative_path(__file__, "snapshot_0_7_6_pre_add_pipeline_snapshot/sqlite")
    with copy_directory(src_dir) as test_dir:
        # invariant check to make sure migration has not been run yet

        db_path = os.path.join(test_dir, "history", "runs.db")

        assert get_current_alembic_version(db_path) == "9fe9e746268c"

        assert "snapshots" not in get_sqlite3_tables(db_path)

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))

        @op
        def noop_op(_):
            pass

        @job
        def noop_job():
            noop_op()

        with pytest.raises(
            (db.exc.OperationalError, db.exc.ProgrammingError, db.exc.StatementError)
        ):
            noop_job.execute_in_process(instance=instance)

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
        assert run.job_snapshot_id is None

        result = noop_job.execute_in_process(instance=instance)

        assert result.success

        runs = instance.get_runs()
        assert len(runs) == 2

        new_run_id = result.run_id

        new_run = instance.get_run_by_id(new_run_id)

        assert new_run.job_snapshot_id


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
            debug_payload = deserialize_value(blob, DebugRunPayload)

            debug_payloads.append(debug_payload)

    return DagsterInstance.ephemeral(preload=debug_payloads)


def test_object_store_operation_result_data_new_fields():
    """We added address and version fields to ObjectStoreOperationResultData.
    Make sure we can still deserialize old ObjectStoreOperationResultData without those fields.
    """
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


def test_mode_column_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_11_16_pre_add_mode_column/sqlite")
    with copy_directory(src_dir) as test_dir:

        @job
        def _test():
            pass

        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "72686963a802"
        assert "mode" not in set(get_sqlite3_columns(db_path, "runs"))

        # this migration was optional, so make sure things work before migrating
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        assert "mode" not in set(get_sqlite3_columns(db_path, "runs"))
        assert instance.get_run_records()
        assert instance.create_run_for_job(_test)

        instance.upgrade()

        # Make sure the schema is migrated
        assert "mode" in set(get_sqlite3_columns(db_path, "runs"))
        assert instance.get_run_records()
        assert instance.create_run_for_job(_test)

        instance._run_storage._alembic_downgrade(rev="72686963a802")

        assert get_current_alembic_version(db_path) == "72686963a802"
        assert "mode" not in set(get_sqlite3_columns(db_path, "runs"))


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
        from dagster._core.storage.runs.migration import RUN_PARTITIONS
        from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

        # load db that has migrated schema, but not populated data for run partitions
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "375e95bad550"

        # Make sure the schema is migrated
        assert "partition" in set(get_sqlite3_columns(db_path, "runs"))
        assert "partition_set" in set(get_sqlite3_columns(db_path, "runs"))

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            with upgrading_instance(instance):
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
        run_storage.migrate(force_rebuild_all=True)

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

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance.upgrade()

        assert "schedules" not in get_sqlite3_tables(db_path)
        assert "schedule_ticks" not in get_sqlite3_tables(db_path)

        assert "jobs" in get_sqlite3_tables(db_path)
        assert "job_ticks" in get_sqlite3_tables(db_path)

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as upgraded_instance:
            assert len(upgraded_instance.all_instigator_state()) == 0


def test_0_10_6_add_bulk_actions_table():
    src_dir = file_relative_path(__file__, "snapshot_0_10_6_add_bulk_actions_table/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "0da417ae1b81"
        assert "bulk_actions" not in get_sqlite3_tables(db_path)
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance.upgrade()
            assert "bulk_actions" in get_sqlite3_tables(db_path)


def test_0_11_0_add_asset_columns():
    src_dir = file_relative_path(__file__, "snapshot_0_11_0_pre_asset_details/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs", "index.db")
        assert get_current_alembic_version(db_path) == "0da417ae1b81"
        assert "last_materialization" not in set(get_sqlite3_columns(db_path, "asset_keys"))
        assert "last_run_id" not in set(get_sqlite3_columns(db_path, "asset_keys"))
        assert "asset_details" not in get_sqlite3_tables(db_path)
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance.upgrade()
            assert "last_materialization" in set(get_sqlite3_columns(db_path, "asset_keys"))
            assert "last_run_id" in set(get_sqlite3_columns(db_path, "asset_keys"))
            assert "asset_details" in set(get_sqlite3_columns(db_path, "asset_keys"))


def test_rename_event_log_entry():
    old_event_record = """{"__class__":"EventRecord","dagster_event":{"__class__":"DagsterEvent","event_specific_data":null,"event_type_value":"PIPELINE_SUCCESS","logging_tags":{},"message":"Finished execution of pipeline.","pid":71356,"pipeline_name":"error_monster","solid_handle":null,"step_handle":null,"step_key":null,"step_kind_value":null},"error_info":null,"level":10,"message":"error_monster - 4be295b5-fcf2-47cc-8e90-cb14d3cf3ac7 - 71356 - PIPELINE_SUCCESS - Finished execution of pipeline.","pipeline_name":"error_monster","run_id":"4be295b5-fcf2-47cc-8e90-cb14d3cf3ac7","step_key":null,"timestamp":1622659924.037028,"user_message":"Finished execution of pipeline."}"""
    event_log_entry = deserialize_value(old_event_record, EventLogEntry)
    dagster_event = event_log_entry.dagster_event
    assert isinstance(dagster_event, DagsterEvent)
    assert dagster_event.event_type_value == "PIPELINE_SUCCESS"


def test_0_12_0_extract_asset_index_cols():
    src_dir = file_relative_path(__file__, "snapshot_0_12_0_pre_asset_index_cols/sqlite")

    @op
    def asset_op(_):
        yield AssetMaterialization(asset_key=AssetKey(["a"]), partition="partition_1")
        yield AssetMaterialization(asset_key=AssetKey(["b"]))
        yield Output(1)

    @job
    def asset_job():
        asset_op()

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs", "index.db")
        assert get_current_alembic_version(db_path) == "3b529ad30626"
        assert "last_materialization_timestamp" not in set(
            get_sqlite3_columns(db_path, "asset_keys")
        )
        assert "wipe_timestamp" not in set(get_sqlite3_columns(db_path, "asset_keys"))
        assert "tags" not in set(get_sqlite3_columns(db_path, "asset_keys"))
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            storage = instance._event_storage

            # make sure that executing the job works
            asset_job.execute_in_process(instance=instance)
            assert storage.has_asset_key(AssetKey(["a"]))
            assert storage.has_asset_key(AssetKey(["b"]))

            # make sure that wiping works
            storage.wipe_asset(AssetKey(["a"]))
            assert not storage.has_asset_key(AssetKey(["a"]))
            assert storage.has_asset_key(AssetKey(["b"]))

            asset_job.execute_in_process(instance=instance)
            assert storage.has_asset_key(AssetKey(["a"]))

            # wipe and leave asset wiped
            storage.wipe_asset(AssetKey(["b"]))
            assert not storage.has_asset_key(AssetKey(["b"]))

            old_keys = storage.all_asset_keys()

            instance.upgrade()

            assert "last_materialization_timestamp" in set(
                get_sqlite3_columns(db_path, "asset_keys")
            )
            assert "wipe_timestamp" in set(get_sqlite3_columns(db_path, "asset_keys"))
            assert "tags" in set(get_sqlite3_columns(db_path, "asset_keys"))

            assert storage.has_asset_key(AssetKey(["a"]))
            assert not storage.has_asset_key(AssetKey(["b"]))

            new_keys = storage.all_asset_keys()
            assert set(old_keys) == set(new_keys)

            # make sure that storing assets still works
            asset_job.execute_in_process(instance=instance)

            # make sure that wiping still works
            storage.wipe_asset(AssetKey(["a"]))
            assert not storage.has_asset_key(AssetKey(["a"]))


def test_op_handle_node_handle():
    # serialize in current code
    test_handle = NodeHandle("test", None)
    test_str = serialize_value(test_handle)

    # deserialize in "legacy" code
    legacy_env = WhitelistMap.create()

    @_whitelist_for_serdes(legacy_env)
    class SolidHandle(namedtuple("_SolidHandle", "name parent")):
        pass

    result = deserialize_value(test_str, whitelist_map=legacy_env)
    assert isinstance(result, SolidHandle)
    assert result.name == test_handle.name


def test_job_run_dagster_run():
    # serialize in current code
    test_run = DagsterRun(job_name="test")
    test_str = serialize_value(test_run)

    # deserialize in "legacy" code
    legacy_env = WhitelistMap.create()

    @_whitelist_for_serdes(legacy_env)
    class PipelineRun(
        namedtuple(
            "_PipelineRun",
            "pipeline_name run_id run_config mode solid_selection solids_to_execute "
            "step_keys_to_execute status tags root_run_id parent_run_id "
            "pipeline_snapshot_id execution_plan_snapshot_id external_pipeline_origin "
            "pipeline_code_origin",
        )
    ):
        pass

    @_whitelist_for_serdes(legacy_env)
    class PipelineRunStatus(Enum):
        QUEUED = "QUEUED"
        NOT_STARTED = "NOT_STARTED"

    result = deserialize_value(test_str, whitelist_map=legacy_env)
    assert isinstance(result, PipelineRun)
    assert result.pipeline_name == test_run.job_name


def test_job_run_status_dagster_run_status():
    # serialize in current code
    test_status = DagsterRunStatus("QUEUED")
    test_str = serialize_value(test_status)

    # deserialize in "legacy" code
    legacy_env = WhitelistMap.create()

    @_whitelist_for_serdes(legacy_env)
    class PipelineRunStatus(Enum):
        QUEUED = "QUEUED"

    result = deserialize_value(test_str, whitelist_map=legacy_env)
    assert isinstance(result, PipelineRunStatus)
    assert result.value == test_status.value


def test_start_time_end_time():
    src_dir = file_relative_path(__file__, "snapshot_0_13_12_pre_add_start_time_and_end_time")
    with copy_directory(src_dir) as test_dir:

        @job
        def _test():
            pass

        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "7f2b1a4ca7a5"
        assert "start_time" not in set(get_sqlite3_columns(db_path, "runs"))
        assert "end_time" not in set(get_sqlite3_columns(db_path, "runs"))

        # this migration was optional, so make sure things work before migrating
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(test_dir))
        assert "start_time" not in set(get_sqlite3_columns(db_path, "runs"))
        assert "end_time" not in set(get_sqlite3_columns(db_path, "runs"))
        assert instance.get_run_records()
        assert instance.create_run_for_job(_test)

        instance.upgrade()

        # Make sure the schema is migrated
        assert "start_time" in set(get_sqlite3_columns(db_path, "runs"))
        assert instance.get_run_records()
        assert instance.create_run_for_job(_test)

        instance._run_storage._alembic_downgrade(rev="7f2b1a4ca7a5")

        assert get_current_alembic_version(db_path) == "7f2b1a4ca7a5"
        assert True


def test_remote_job_origin_instigator_origin():
    def build_legacy_whitelist_map():
        legacy_env = WhitelistMap.create()

        @_whitelist_for_serdes(legacy_env)
        class ExternalJobOrigin(
            namedtuple("_ExternalJobOrigin", "external_repository_origin job_name")
        ):
            def get_id(self):
                return create_snapshot_id(self, legacy_env)

        @_whitelist_for_serdes(legacy_env)
        class ExternalRepositoryOrigin(
            namedtuple(
                "_ExternalRepositoryOrigin",
                "repository_location_origin repository_name",
            )
        ):
            def get_id(self):
                return create_snapshot_id(self)

        @_whitelist_for_serdes(whitelist_map=legacy_env, skip_when_empty_fields={"use_ssl"})
        class GrpcServerRepositoryLocationOrigin(
            namedtuple(
                "_GrpcServerRepositoryLocationOrigin",
                "host port socket location_name use_ssl",
            ),
        ):
            def __new__(cls, host, port=None, socket=None, location_name=None, use_ssl=None):
                return super(GrpcServerRepositoryLocationOrigin, cls).__new__(
                    cls, host, port, socket, location_name, use_ssl
                )

        return (
            legacy_env,
            ExternalJobOrigin,
            ExternalRepositoryOrigin,
            GrpcServerRepositoryLocationOrigin,
        )

    legacy_env, klass, repo_klass, location_klass = build_legacy_whitelist_map()

    from dagster._core.remote_representation.origin import (
        GrpcServerCodeLocationOrigin,
        RemoteInstigatorOrigin,
        RemoteRepositoryOrigin,
    )

    # serialize from current code, compare against old code
    instigator_origin = RemoteInstigatorOrigin(
        repository_origin=RemoteRepositoryOrigin(
            code_location_origin=GrpcServerCodeLocationOrigin(
                host="localhost", port=1234, location_name="test_location"
            ),
            repository_name="the_repo",
        ),
        instigator_name="simple_schedule",
    )
    instigator_origin_str = serialize_value(instigator_origin)
    instigator_to_job = deserialize_value(instigator_origin_str, whitelist_map=legacy_env)
    assert isinstance(instigator_to_job, klass)
    # ensure that the origin id is stable
    assert instigator_to_job.get_id() == instigator_origin.get_id()

    # # serialize from old code, compare against current code
    job_origin = klass(
        external_repository_origin=repo_klass(
            repository_location_origin=location_klass(
                host="localhost", port=1234, location_name="test_location"
            ),
            repository_name="the_repo",
        ),
        job_name="simple_schedule",
    )
    job_origin_str = serialize_value(job_origin, legacy_env)

    job_to_instigator = deserialize_value(job_origin_str, RemoteInstigatorOrigin)
    # ensure that the origin id is stable
    assert job_to_instigator.get_id() == job_origin.get_id()


def test_schedule_namedtuple_job_instigator_backcompat():
    src_dir = file_relative_path(__file__, "snapshot_0_13_19_instigator_named_tuples/sqlite")
    with copy_directory(src_dir) as test_dir:
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            states = instance.all_instigator_state()
            assert len(states) == 2
            check.is_list(states, of_type=InstigatorState)
            for state in states:
                assert state.instigator_type
                assert state.instigator_data
                ticks = instance.get_ticks(state.instigator_origin_id, state.selector_id)
                check.is_list(ticks, of_type=InstigatorTick)
                for tick in ticks:
                    assert tick.tick_data
                    assert tick.instigator_type
                    assert tick.instigator_name


def test_legacy_event_log_load():
    # ensure EventLogEntry 0.14.3+ can still be loaded by older dagster versions
    # to avoid downgrades etc from creating operational issues
    legacy_env = WhitelistMap.create()

    # snapshot of EventLogEntry pre commit ea19544
    @_whitelist_for_serdes(
        whitelist_map=legacy_env,
        storage_name="EventLogEntry",  # use this to avoid collision with current EventLogEntry
    )
    class OldEventLogEntry(
        NamedTuple(
            "_OldEventLogEntry",
            [
                ("error_info", Optional[SerializableErrorInfo]),
                ("message", str),
                ("level", Union[str, int]),
                ("user_message", str),
                ("run_id", str),
                ("timestamp", float),
                ("step_key", Optional[str]),
                ("pipeline_name", Optional[str]),
                ("dagster_event", Optional[DagsterEvent]),
            ],
        )
    ):
        def __new__(
            cls,
            error_info,
            message,
            level,
            user_message,
            run_id,
            timestamp,
            step_key=None,
            pipeline_name=None,
            dagster_event=None,
            job_name=None,
        ):
            pipeline_name = pipeline_name or job_name
            return super().__new__(
                cls,
                check.opt_inst_param(error_info, "error_info", SerializableErrorInfo),
                check.str_param(message, "message"),
                level,  # coerce_valid_log_level call omitted
                check.str_param(user_message, "user_message"),
                check.str_param(run_id, "run_id"),
                check.float_param(timestamp, "timestamp"),
                check.opt_str_param(step_key, "step_key"),
                check.opt_str_param(pipeline_name, "pipeline_name"),
                check.opt_inst_param(dagster_event, "dagster_event", DagsterEvent),
            )

    # current event log entry
    new_event = EventLogEntry(
        user_message="test 1 2 3",
        error_info=None,
        level="debug",
        run_id="fake_run_id",
        timestamp=time.time(),
    )

    storage_str = serialize_value(new_event)

    result = deserialize_value(storage_str, OldEventLogEntry, whitelist_map=legacy_env)
    assert result.message is not None


def test_schedule_secondary_index_table_backcompat():
    src_dir = file_relative_path(__file__, "snapshot_0_14_6_schedule_migration_table/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "schedules", "schedules.db")

        assert get_current_alembic_version(db_path) == "0da417ae1b81"

        assert "secondary_indexes" not in get_sqlite3_tables(db_path)

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance.upgrade()

        assert "secondary_indexes" in get_sqlite3_tables(db_path)


def test_instigators_table_backcompat():
    src_dir = file_relative_path(__file__, "snapshot_0_14_6_instigators_table/sqlite")
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "schedules", "schedules.db")

        assert get_current_alembic_version(db_path) == "54666da3db5c"

        assert "instigators" not in get_sqlite3_tables(db_path)
        assert "selector_id" not in set(get_sqlite3_columns(db_path, "jobs"))
        assert "selector_id" not in set(get_sqlite3_columns(db_path, "job_ticks"))

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance.upgrade()

        assert "instigators" in get_sqlite3_tables(db_path)
        assert "selector_id" in set(get_sqlite3_columns(db_path, "jobs"))
        assert "selector_id" in set(get_sqlite3_columns(db_path, "job_ticks"))


def test_jobs_selector_id_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration/sqlite")

    from dagster._core.storage.schedules.migration import SCHEDULE_JOBS_SELECTOR_ID
    from dagster._core.storage.schedules.schema import InstigatorsTable, JobTable, JobTickTable

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "schedules", "schedules.db")

        assert get_current_alembic_version(db_path) == "c892b3fe0a9f"

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
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


def test_tick_selector_index_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_14_6_post_schema_pre_data_migration/sqlite")

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "schedules", "schedules.db")

        assert get_current_alembic_version(db_path) == "c892b3fe0a9f"

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert "idx_tick_selector_timestamp" not in get_sqlite3_indexes(db_path, "job_ticks")
            instance.upgrade()
            assert "idx_tick_selector_timestamp" in get_sqlite3_indexes(db_path, "job_ticks")


def test_repo_label_tag_migration():
    src_dir = file_relative_path(__file__, "snapshot_0_14_14_pre_repo_label_tags/sqlite")

    with copy_directory(src_dir) as test_dir:
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            job_repo_filter = RunsFilter(
                job_name="hammer",
                tags={REPOSITORY_LABEL_TAG: "toys_repository@dagster_test.graph_job_op_toys.repo"},
            )

            count = instance.get_runs_count(job_repo_filter)
            assert count == 0

            instance.upgrade()

            count = instance.get_runs_count(job_repo_filter)
            assert count == 2


def test_add_bulk_actions_columns():
    from dagster._core.remote_representation.origin import (
        GrpcServerCodeLocationOrigin,
        RemotePartitionSetOrigin,
        RemoteRepositoryOrigin,
    )
    from dagster._core.storage.runs.schema import BulkActionsTable

    src_dir = file_relative_path(__file__, "snapshot_0_14_16_bulk_actions_columns/sqlite")

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert {"id", "key", "status", "timestamp", "body"} == set(
            get_sqlite3_columns(db_path, "bulk_actions")
        )
        assert "idx_bulk_actions_action_type" not in get_sqlite3_indexes(db_path, "bulk_actions")
        assert "idx_bulk_actions_selector_id" not in get_sqlite3_indexes(db_path, "bulk_actions")

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            instance.upgrade()

            assert {
                "id",
                "key",
                "status",
                "timestamp",
                "body",
                "action_type",
                "selector_id",
            } == set(get_sqlite3_columns(db_path, "bulk_actions"))
            assert "idx_bulk_actions_action_type" in get_sqlite3_indexes(db_path, "bulk_actions")
            assert "idx_bulk_actions_selector_id" in get_sqlite3_indexes(db_path, "bulk_actions")

            # check data migration
            backfill_count = len(instance.get_backfills())
            migrated_row_count = instance._run_storage.fetchone(
                db_select([db.func.count().label("count")])
                .select_from(BulkActionsTable)
                .where(BulkActionsTable.c.selector_id.isnot(None))
            )["count"]
            assert migrated_row_count > 0
            assert backfill_count == migrated_row_count

            # check that we are writing to selector id, action types
            remote_origin = RemotePartitionSetOrigin(
                repository_origin=RemoteRepositoryOrigin(
                    code_location_origin=GrpcServerCodeLocationOrigin(port=1234, host="localhost"),
                    repository_name="fake_repository",
                ),
                partition_set_name="fake",
            )
            instance.add_backfill(
                PartitionBackfill(
                    backfill_id="simple",
                    partition_set_origin=remote_origin,
                    status=BulkActionStatus.REQUESTED,
                    partition_names=["one", "two", "three"],
                    from_failure=False,
                    reexecution_steps=None,
                    tags=None,
                    backfill_timestamp=get_current_timestamp(),
                )
            )
            unmigrated_row_count = instance._run_storage.fetchone(
                db_select([db.func.count().label("count")])
                .select_from(BulkActionsTable)
                .where(BulkActionsTable.c.selector_id.is_(None))
            )["count"]
            assert unmigrated_row_count == 0

            # test downgrade
            instance._run_storage._alembic_downgrade(rev="721d858e1dda")

            assert get_current_alembic_version(db_path) == "721d858e1dda"
            assert {"id", "key", "status", "timestamp", "body"} == set(
                get_sqlite3_columns(db_path, "bulk_actions")
            )
            assert "idx_bulk_actions_action_type" not in get_sqlite3_indexes(
                db_path, "bulk_actions"
            )
            assert "idx_bulk_actions_selector_id" not in get_sqlite3_indexes(
                db_path, "bulk_actions"
            )


def test_add_kvs_table():
    src_dir = file_relative_path(__file__, "snapshot_0_14_16_bulk_actions_columns/sqlite")

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert "kvs" not in get_sqlite3_tables(db_path)
            assert get_sqlite3_indexes(db_path, "kvs") == []

            instance.upgrade()

            assert "kvs" in get_sqlite3_tables(db_path)
            assert get_sqlite3_indexes(db_path, "kvs") == ["idx_kvs_keys_unique"]
            instance._run_storage._alembic_downgrade(rev="6860f830e40c")

            assert "kvs" not in get_sqlite3_tables(db_path)
            assert get_sqlite3_indexes(db_path, "kvs") == []


def test_add_asset_event_tags_table():
    @op
    def yields_materialization_w_tags(_):
        yield AssetMaterialization(asset_key=AssetKey(["a"]), tags={DATA_VERSION_TAG: "bar"})
        yield Output(1)

    @job
    def asset_job():
        yields_materialization_w_tags()

    src_dir = file_relative_path(__file__, "snapshot_1_0_12_pre_add_asset_event_tags_table/sqlite")

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert "asset_event_tags" not in get_sqlite3_tables(db_path)

            asset_job.execute_in_process(instance=instance)
            with pytest.raises(
                DagsterInvalidInvocationError, match="In order to search for asset event tags"
            ):
                instance._event_storage.get_event_tags_for_asset(asset_key=AssetKey(["a"]))

            assert get_sqlite3_indexes(db_path, "asset_event_tags") == []

            instance.upgrade()

            assert "asset_event_tags" in get_sqlite3_tables(db_path)

            asset_job.execute_in_process(instance=instance)
            assert instance._event_storage.get_event_tags_for_asset(asset_key=AssetKey(["a"])) == [
                {DATA_VERSION_TAG: "bar"}
            ]

            indexes = get_sqlite3_indexes(db_path, "asset_event_tags")
            assert "idx_asset_event_tags_event_id" in indexes
            assert "idx_asset_event_tags" in indexes

            instance._run_storage._alembic_downgrade(rev="a00dd8d936a1")

            assert "asset_event_tags" not in get_sqlite3_tables(db_path)
            assert get_sqlite3_indexes(db_path, "asset_event_tags") == []


def test_1_0_17_add_cached_status_data_column():
    src_dir = file_relative_path(
        __file__, "snapshot_1_0_17_pre_add_cached_status_data_column/sqlite"
    )
    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs", "index.db")
        assert get_current_alembic_version(db_path) == "958a9495162d"
        assert "cached_status_data" not in set(get_sqlite3_columns(db_path, "asset_keys"))
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert instance.can_read_asset_status_cache() is False
            instance.upgrade()
            assert "cached_status_data" in set(get_sqlite3_columns(db_path, "asset_keys"))


def test_add_dynamic_partitions_table():
    src_dir = file_relative_path(
        __file__, "snapshot_1_0_17_pre_add_cached_status_data_column/sqlite"
    )

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs", "index.db")
        assert get_current_alembic_version(db_path) == "958a9495162d"

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert "dynamic_partitions" not in get_sqlite3_tables(db_path)

            instance.wipe()

            with pytest.raises(DagsterInvalidInvocationError, match="does not exist"):
                instance.get_dynamic_partitions("foo")

            instance.upgrade()
            assert "dynamic_partitions" in get_sqlite3_tables(db_path)
            assert instance.get_dynamic_partitions("foo") == []


def _get_table_row_count(run_storage, table, with_non_null_id=False):
    query = db_select([db.func.count()]).select_from(table)
    if with_non_null_id:
        query = query.where(table.c.id.isnot(None))
    with run_storage.connect() as conn:
        row_count = conn.execute(query).fetchone()[0]
    return row_count


def test_add_primary_keys():
    from dagster._core.storage.runs.schema import (
        DaemonHeartbeatsTable,
        InstanceInfo,
        KeyValueStoreTable,
    )

    src_dir = file_relative_path(__file__, "snapshot_1_1_22_pre_primary_key/sqlite")

    with copy_directory(src_dir) as test_dir:
        db_path = os.path.join(test_dir, "history", "runs.db")
        assert get_current_alembic_version(db_path) == "e62c379ac8f4"

        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            assert "id" not in set(get_sqlite3_columns(db_path, "kvs"))
            # trigger insert, and update
            instance.run_storage.set_cursor_values({"a": "A"})
            instance.run_storage.set_cursor_values({"a": "A"})
            kvs_row_count = _get_table_row_count(instance.run_storage, KeyValueStoreTable)
            assert kvs_row_count > 0

            assert "id" not in set(get_sqlite3_columns(db_path, "instance_info"))
            instance_info_row_count = _get_table_row_count(instance.run_storage, InstanceInfo)
            assert instance_info_row_count > 0

            assert "id" not in set(get_sqlite3_columns(db_path, "daemon_heartbeats"))
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

            assert "id" in set(get_sqlite3_columns(db_path, "kvs"))
            with instance.run_storage.connect():
                kvs_id_count = _get_table_row_count(
                    instance.run_storage, KeyValueStoreTable, with_non_null_id=True
                )
            assert kvs_id_count == kvs_row_count

            assert "id" in set(get_sqlite3_columns(db_path, "instance_info"))
            with instance.run_storage.connect():
                instance_info_id_count = _get_table_row_count(
                    instance.run_storage, InstanceInfo, with_non_null_id=True
                )
            assert instance_info_id_count == instance_info_row_count

            assert "id" in set(get_sqlite3_columns(db_path, "daemon_heartbeats"))
            with instance.run_storage.connect():
                daemon_heartbeats_id_count = _get_table_row_count(
                    instance.run_storage, DaemonHeartbeatsTable, with_non_null_id=True
                )
            assert daemon_heartbeats_id_count == daemon_heartbeats_row_count


# Prior to 0.10.0, it was possible to have `Materialization` events with no asset key.
# `AssetMaterialization` is _supposed_ to runtime-check for null `AssetKey`, but it doesn't, so we
# can deserialize a `Materialization` with a null asset key directly to an `AssetMaterialization`.
# In the future, we will need to enable the runtime null check on `AssetMaterialization` and
# introduce a dummy asset key when deserializing old `Materialization` events.
@pytest.mark.parametrize(
    "asset_key", [AssetKey(["foo", "bar"]), None, "__missing__"], ids=("defined", "none", "missing")
)
def test_load_old_materialization(asset_key: Optional[AssetKey]):
    packed_asset_key = pack_value(asset_key) if isinstance(asset_key, AssetKey) else None
    delete_asset_key = asset_key == "__missing__"
    packed_old_materialization = {
        "__class__": "StepMaterializationData",
        "materialization": {
            "__class__": "Materialization",
            "label": "foo",
            "description": "bar",
            "metadata_entries": [
                {
                    "__class__": "EventMetadataEntry",
                    "label": "baz",
                    "description": "qux",
                    "entry_data": {
                        "__class__": "TextMetadataEntryData",
                        "text": "quux",
                    },
                }
            ],
            "partition": "alpha",
            "asset_key": packed_asset_key,  # this key will be deleted for `__missing__`
        },
        "asset_lineage": [
            {
                "__class__": "AssetLineageInfo",
                "asset_key": {"__class__": "AssetKey", "path": ["foo", "bar"]},
                "partitions": {"__set__": ["alpha"]},
            }
        ],
    }
    if delete_asset_key:
        del packed_old_materialization["materialization"]["asset_key"]
    old_materialization = serialize_value(packed_old_materialization)

    deserialized_asset_key = (
        AssetKey(UNDEFINED_ASSET_KEY_PATH) if asset_key in (None, "__missing__") else asset_key
    )
    assert deserialize_value(
        old_materialization, StepMaterializationData
    ) == StepMaterializationData(
        materialization=AssetMaterialization(
            description="bar",
            metadata={"baz": MetadataValue.text("quux")},
            partition="alpha",
            asset_key=deserialized_asset_key,
        ),
        asset_lineage=[AssetLineageInfo(asset_key=AssetKey(["foo", "bar"]), partitions={"alpha"})],
    )


# Prior to 1.2.5, metadata was stored on all classes as a `List[MetadataEntry]`. With 1.2.5 it
# changed to `Dict[str, MetadataValue]`, with serdes-whitelisted classes using
# `MetadataFieldSerializer` to serialize the dictionary as a list of `MetadataEntry` for backcompat.
def test_metadata_serialization():
    # We use `AssetMaterialization` as a stand-in for all classes using `MetadataFieldSerializer`.
    mat = AssetMaterialization(
        AssetKey(["foo"]),
        metadata={"alpha": MetadataValue.text("beta"), "delta": MetadataValue.int(1)},
    )
    serialized_mat = serialize_value(mat)
    assert json.loads(serialized_mat)["metadata_entries"] == [
        {
            "__class__": "EventMetadataEntry",
            "label": "alpha",
            "description": None,
            "entry_data": {"__class__": "TextMetadataEntryData", "text": "beta"},
        },
        {
            "__class__": "EventMetadataEntry",
            "label": "delta",
            "description": None,
            "entry_data": {"__class__": "IntMetadataEntryData", "value": 1},
        },
    ]
    assert deserialize_value(serialized_mat, AssetMaterialization) == mat


# When receiving pre-1.4 static partitions definitions from user code, it is possible they contain
# duplicates. We need to de-dup them at the serdes/"External" layer before reconstructing the
# partitions definition in the host process to avoid an error.
def test_static_partitions_definition_dup_keys_backcompat():
    received_from_user = StaticPartitionsSnap(partition_keys=["a", "b", "a"])
    assert received_from_user.get_partitions_definition() == StaticPartitionsDefinition(
        partition_keys=["a", "b"]
    )


# 1.6.13 added a custom field serializer to KnownExecutionState.step_output_versions and deleted the
# class `StepOutputVersionData`, but we still serialize to `StepOutputVersionData` for backcompat.
def test_known_execution_state_step_output_version_serialization() -> None:
    known_state = KnownExecutionState(
        previous_retry_attempts=None,
        dynamic_mappings=None,
        step_output_versions={StepOutputHandle("foo", "bar"): "1"},
    )

    serialized = serialize_value(known_state)
    assert json.loads(serialized)["step_output_versions"] == [
        {
            "__class__": "StepOutputVersionData",
            "step_output_handle": {
                "__class__": "StepOutputHandle",
                "step_key": "foo",
                "output_name": "bar",
                "mapping_key": None,
            },
            "version": "1",
        }
    ]

    assert deserialize_value(serialized, KnownExecutionState) == known_state


def test_legacy_compute_kind_tag_backcompat() -> None:
    legacy_tags = {LEGACY_COMPUTE_KIND_TAG: "foo"}
    with pytest.warns(DeprecationWarning, match="Legacy compute kind tag"):

        @asset(op_tags=legacy_tags)
        def legacy_asset():
            pass

        assert legacy_asset.op.tags[COMPUTE_KIND_TAG] == "foo"

    with pytest.warns(DeprecationWarning, match="Legacy compute kind tag"):

        @op(tags=legacy_tags)
        def legacy_op():
            pass

        assert legacy_op.tags[COMPUTE_KIND_TAG] == "foo"

    legacy_snap_path = file_relative_path(__file__, "1_7_9_kind_op_job_snap.gz")
    legacy_snap = deserialize_value(
        GzipFile(legacy_snap_path, mode="r").read().decode("utf-8"), JobSnap
    )
    assert create_snapshot_id(legacy_snap) == "8db90f128b7eaa5c229bdde372e39d5cbecdc7e4"
