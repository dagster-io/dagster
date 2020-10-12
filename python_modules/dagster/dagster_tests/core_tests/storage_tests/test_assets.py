from contextlib import contextmanager

import pytest

from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterEventType,
    Output,
    execute_pipeline,
    pipeline,
    seven,
    solid,
)
from dagster.core.definitions.events import (
    parse_asset_key_string,
    validate_asset_key_string,
    validate_structured_asset_key,
)
from dagster.core.errors import DagsterInvalidAssetKey
from dagster.core.events.log import EventRecord
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
)
from dagster.core.storage.event_log.migration import migrate_asset_key_data
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage


def get_instance(temp_dir, event_log_storage):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=event_log_storage,
        compute_log_manager=NoOpComputeLogManager(),
        run_launcher=SyncInMemoryRunLauncher(),
    )


@contextmanager
def create_in_memory_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        asset_storage = InMemoryEventLogStorage()
        instance = get_instance(temp_dir, asset_storage)
        yield [instance, asset_storage]


@contextmanager
def create_consolidated_sqlite_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        asset_storage = ConsolidatedSqliteEventLogStorage(temp_dir)
        instance = get_instance(temp_dir, asset_storage)
        yield [instance, asset_storage]


asset_test = pytest.mark.parametrize(
    "asset_aware_context",
    [create_in_memory_event_log_instance, create_consolidated_sqlite_event_log_instance,],
)


@solid
def solid_one(_):
    yield AssetMaterialization(asset_key=AssetKey("asset_1"))
    yield Output(1)


@solid
def solid_two(_):
    yield AssetMaterialization(asset_key=AssetKey("asset_2"))
    yield AssetMaterialization(asset_key=AssetKey(["path", "to", "asset_3"]))
    yield Output(1)


@solid
def solid_normalization(_):
    yield AssetMaterialization(asset_key="path/to-asset_4")
    yield Output(1)


@pipeline
def pipeline_one():
    solid_one()


@pipeline
def pipeline_two():
    solid_one()
    solid_two()


@pipeline
def pipeline_normalization():
    solid_normalization()


def test_validate_asset_key_string():
    assert validate_asset_key_string("H3_lL0.h-1") == "H3_lL0.h-1"
    with pytest.raises(DagsterInvalidAssetKey):
        validate_asset_key_string("(Hello)")


def test_parse_asset_key_string():
    assert parse_asset_key_string("foo.bar_b-az") == ["foo", "bar_b", "az"]


def test_validate_structured_asset_key():
    asset_key_valid = ["f0-O", "b4_r"]
    assert asset_key_valid == validate_structured_asset_key(asset_key_valid)
    asset_key_invalid = ["(foo)"]
    with pytest.raises(DagsterInvalidAssetKey):
        validate_structured_asset_key(asset_key_invalid)


@asset_test
def test_asset_keys(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 3
        assert set([asset_key.to_string() for asset_key in asset_keys]) == set(
            ["asset_1", "asset_2", "path.to.asset_3"]
        )
        prefixed_keys = event_log_storage.get_all_asset_keys(prefix_path=["asset"])
        assert len(prefixed_keys) == 2


@asset_test
def test_has_asset_key(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        assert event_log_storage.has_asset_key(AssetKey(["path", "to", "asset_3"]))
        assert not event_log_storage.has_asset_key(AssetKey(["path", "to", "bogus", "asset"]))


@asset_test
def test_asset_events(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_events = event_log_storage.get_asset_events(AssetKey("asset_1"))
        assert len(asset_events) == 2
        for event in asset_events:
            assert isinstance(event, EventRecord)
            assert event.is_dagster_event
            assert event.dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION
            assert event.dagster_event.asset_key

        asset_events = event_log_storage.get_asset_events(AssetKey(["path", "to", "asset_3"]))
        assert len(asset_events) == 1


@asset_test
def test_asset_run_ids(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        one = execute_pipeline(pipeline_one, instance=instance)
        two = execute_pipeline(pipeline_two, instance=instance)
        run_ids = event_log_storage.get_asset_run_ids(AssetKey("asset_1"))
        assert set(run_ids) == set([one.run_id, two.run_id])


@asset_test
def test_asset_normalization(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_normalization, instance=instance)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 1
        asset_key = asset_keys[0]
        assert asset_key.to_string() == "path.to.asset_4"
        assert asset_key.path == ["path", "to", "asset_4"]


@asset_test
def test_asset_wipe(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        one = execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 3
        log_count = len(event_log_storage.get_logs_for_run(one.run_id))
        instance.wipe_assets(asset_keys)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 0
        assert log_count == len(event_log_storage.get_logs_for_run(one.run_id))

        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 3
        instance.wipe_assets([AssetKey(["path", "to", "asset_3"])])
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 2


@asset_test
def test_asset_secondary_index(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_one, instance=instance)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 1
        migrate_asset_key_data(event_log_storage)
        two = execute_pipeline(pipeline_two, instance=instance)
        two_two = execute_pipeline(pipeline_two, instance=instance)

        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 3

        event_log_storage.delete_events(two.run_id)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 3

        event_log_storage.delete_events(two_two.run_id)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 1
