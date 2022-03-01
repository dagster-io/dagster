import tempfile
import time
from contextlib import contextmanager

import pytest

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DagsterEventType,
    EventRecordsFilter,
    Field,
    Output,
    execute_pipeline,
    job,
    op,
    pipeline,
    solid,
)
from dagster.core.definitions.events import parse_asset_key_string, validate_asset_key_string
from dagster.core.errors import DagsterInvalidAssetKey
from dagster.core.events import DagsterEvent, StepMaterializationData
from dagster.core.events.log import EventLogEntry
from dagster.core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
    SqliteEventLogStorage,
)
from dagster.core.storage.event_log.migration import ASSET_KEY_INDEX_COLS, migrate_asset_key_data
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.utils import file_relative_path
from dagster.utils.test import copy_directory


def test_validate_asset_key_string():
    assert validate_asset_key_string("H3_lL0.h-1") == "H3_lL0.h-1"
    with pytest.raises(DagsterInvalidAssetKey):
        validate_asset_key_string("(Hello)")


def test_structured_asset_key():
    asset_parsed = AssetKey(parse_asset_key_string("(Hello)"))
    assert len(asset_parsed.path) == 1
    assert asset_parsed.path[0] == "Hello"

    asset_structured = AssetKey(["(Hello)"])
    assert len(asset_structured.path) == 1
    assert asset_structured.path[0] == "(Hello)"


def test_parse_asset_key_string():
    assert parse_asset_key_string("foo.bar_b-az") == ["foo", "bar_b", "az"]


def test_backcompat_asset_read():
    src_dir = file_relative_path(__file__, "compat_tests/snapshot_0_11_0_asset_materialization")
    # should contain materialization events for asset keys a, b, c, d, e, f
    # events a and b have been wiped, but b has been rematerialized
    def _validate_instance_assets(instance):
        assert instance.all_asset_keys() == [
            AssetKey("b"),
            AssetKey("c"),
            AssetKey("d"),
            AssetKey("e"),
            AssetKey("f"),
        ]
        assert instance.get_asset_keys() == [
            AssetKey("b"),
            AssetKey("c"),
            AssetKey("d"),
            AssetKey("e"),
            AssetKey("f"),
        ]
        assert instance.get_asset_keys(prefix=["d"]) == [AssetKey("d")]
        assert instance.get_asset_keys(limit=3) == [
            AssetKey("b"),
            AssetKey("c"),
            AssetKey("d"),
        ]
        assert instance.get_asset_keys(cursor='["b"]', limit=3) == [
            AssetKey("c"),
            AssetKey("d"),
            AssetKey("e"),
        ]

    @op
    def materialize():
        yield AssetMaterialization(AssetKey("e"))
        yield AssetMaterialization(AssetKey("f"))
        yield Output(None)

    @job
    def my_job():
        materialize()

    with copy_directory(src_dir) as test_dir:
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            _validate_instance_assets(instance)
            my_job.execute_in_process(instance=instance)
            _validate_instance_assets(instance)
            instance.upgrade()
            _validate_instance_assets(instance)
            my_job.execute_in_process(instance=instance)
            _validate_instance_assets(instance)
            instance.reindex()
            _validate_instance_assets(instance)
            my_job.execute_in_process(instance=instance)
            _validate_instance_assets(instance)


def test_backcompat_asset_materializations():
    src_dir = file_relative_path(__file__, "compat_tests/snapshot_0_11_0_asset_materialization")
    # should contain materialization events for asset keys a, b, c, d, e, f
    # events a and b have been wiped, but b has been rematerialized

    @op
    def materialize():
        yield AssetMaterialization(AssetKey("c"), tags={"foo": "bar"})
        yield Output(None)

    @job
    def my_job():
        materialize()

    def _validate_materialization(asset_key, event, expected_tags):
        assert isinstance(event, EventLogEntry)
        assert event.dagster_event
        assert event.dagster_event.is_step_materialization
        assert event.dagster_event.step_materialization_data.materialization.asset_key == asset_key
        assert event.dagster_event.step_materialization_data.materialization.tags == expected_tags

    a = AssetKey("a")
    b = AssetKey("b")
    c = AssetKey("c")

    with copy_directory(src_dir) as test_dir:
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            storage = instance.event_log_storage

            a_mat = storage.get_latest_materialization_events([a]).get(a)
            assert a_mat is None

            b_mat = storage.get_latest_materialization_events([b]).get(b)
            _validate_materialization(b, b_mat, expected_tags={})

            c_mat = storage.get_latest_materialization_events([c]).get(c)
            _validate_materialization(c, c_mat, expected_tags={})

            mat_by_key = storage.get_latest_materialization_events([a, b, c])
            assert mat_by_key.get(a) is None
            _validate_materialization(b, mat_by_key.get(b), expected_tags={})
            _validate_materialization(c, mat_by_key.get(c), expected_tags={})

            # materialize c with tags
            my_job.execute_in_process(instance=instance)

            a_mat = storage.get_latest_materialization_events([a]).get(a)
            assert a_mat is None

            b_mat = storage.get_latest_materialization_events([b]).get(b)
            _validate_materialization(b, b_mat, expected_tags={})

            c_mat = storage.get_latest_materialization_events([c]).get(c)
            _validate_materialization(c, c_mat, expected_tags={"foo": "bar"})

            mat_by_key = storage.get_latest_materialization_events([a, b, c])
            assert mat_by_key.get(a) is None
            _validate_materialization(b, mat_by_key.get(b), expected_tags={})
            _validate_materialization(c, c_mat, expected_tags={"foo": "bar"})


def test_asset_lazy_migration():
    src_dir = file_relative_path(__file__, "compat_tests/snapshot_0_11_0_asset_materialization")
    # should contain materialization events for asset keys a, b, c, d, e, f
    # events a and b have been wiped, but b has been rematerialized

    @op
    def materialize():
        yield AssetMaterialization(AssetKey("a"))
        yield AssetMaterialization(AssetKey("b"))
        yield AssetMaterialization(AssetKey("c"))
        yield AssetMaterialization(AssetKey("d"))
        yield AssetMaterialization(AssetKey("e"))
        yield AssetMaterialization(AssetKey("f"))
        yield Output(None)

    @job
    def my_job():
        materialize()

    with copy_directory(src_dir) as test_dir:
        with DagsterInstance.from_ref(InstanceRef.from_dir(test_dir)) as instance:
            storage = instance.event_log_storage
            assert not storage.has_asset_key_index_cols()
            assert not storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            # run the schema migration without reindexing the asset keys
            storage.upgrade()
            assert storage.has_asset_key_index_cols()
            assert not storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            # fetch all asset keys
            instance.all_asset_keys()
            assert not storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            # wipe a, b in order to populate wipe_timestamp
            storage.wipe_asset(AssetKey("a"))
            storage.wipe_asset(AssetKey("b"))

            # materialize all the assets to populate materialization_timestamp
            my_job.execute_in_process(instance=instance)

            # still should not be migrated (on write)
            assert not storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            # fetching partial results should not trigger migration
            instance.get_asset_keys(prefix=["b"])
            instance.get_asset_keys(cursor=str(AssetKey("b")))
            instance.get_latest_materialization_events(asset_keys=[AssetKey("b")])

            assert not storage.has_secondary_index(ASSET_KEY_INDEX_COLS)

            # on read, we should see that all the data has already been migrated and we can now mark
            # the asset key index as migrated
            instance.all_asset_keys()
            assert storage.has_secondary_index(ASSET_KEY_INDEX_COLS)
