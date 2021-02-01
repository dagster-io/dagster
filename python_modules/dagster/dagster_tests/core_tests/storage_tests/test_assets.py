import tempfile
import time
from contextlib import contextmanager

import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterEventType,
    Field,
    Output,
    execute_pipeline,
    file_relative_path,
    pipeline,
    solid,
)
from dagster.core.definitions.events import parse_asset_key_string, validate_asset_key_string
from dagster.core.errors import DagsterInvalidAssetKey
from dagster.core.events import DagsterEvent, StepMaterializationData
from dagster.core.events.log import DagsterEventRecord, EventRecord
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
)
from dagster.core.storage.event_log.migration import migrate_asset_key_data
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.utils.test import copy_directory


def get_instance(temp_dir, event_log_storage):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=event_log_storage,
        compute_log_manager=NoOpComputeLogManager(),
        run_coordinator=DefaultRunCoordinator(),
        run_launcher=SyncInMemoryRunLauncher(),
    )


@contextmanager
def create_in_memory_event_log_instance():
    with tempfile.TemporaryDirectory() as temp_dir:
        asset_storage = InMemoryEventLogStorage()
        instance = get_instance(temp_dir, asset_storage)
        yield [instance, asset_storage]


@contextmanager
def create_consolidated_sqlite_event_log_instance():
    with tempfile.TemporaryDirectory() as temp_dir:
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


@solid(config_schema={"partition": Field(str, is_required=False)})
def solid_partitioned(context):
    yield AssetMaterialization(
        asset_key=AssetKey("asset_key"), partition=context.solid_config.get("partition")
    )
    yield Output(1)


@pipeline
def pipeline_partitioned():
    solid_partitioned()


def execute_partitioned_pipeline(instance, partition):
    return execute_pipeline(
        pipeline_partitioned,
        run_config={"solids": {"solid_partitioned": {"config": {"partition": partition}}}},
        instance=instance,
    )


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


@asset_test
def test_asset_keys(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_keys = event_log_storage.get_all_asset_keys()
        assert len(asset_keys) == 3
        assert set([asset_key.to_string() for asset_key in asset_keys]) == set(
            ['["asset_1"]', '["asset_2"]', '["path", "to", "asset_3"]']
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
def test_asset_events_range(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)

        # descending
        asset_events = event_log_storage.get_asset_events(AssetKey("asset_1"), include_cursor=True)
        assert len(asset_events) == 3
        [id_three, id_two, id_one] = [id for id, event in asset_events]

        after_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"), include_cursor=True, after_cursor=id_one
        )
        assert len(after_events) == 2
        assert [id for id, event in after_events] == [id_three, id_two]

        before_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"), include_cursor=True, before_cursor=id_three
        )
        assert len(before_events) == 2
        assert [id for id, event in before_events] == [id_two, id_one]

        between_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"), include_cursor=True, before_cursor=id_three, after_cursor=id_one,
        )
        assert len(between_events) == 1
        assert [id for id, event in between_events] == [id_two]

        # ascending
        asset_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"), include_cursor=True, ascending=True
        )
        assert len(asset_events) == 3
        [id_one, id_two, id_three] = [id for id, event in asset_events]

        after_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"), include_cursor=True, after_cursor=id_one, ascending=True
        )
        assert len(after_events) == 2
        assert [id for id, event in after_events] == [id_two, id_three]

        before_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"), include_cursor=True, before_cursor=id_three, ascending=True
        )
        assert len(before_events) == 2
        assert [id for id, event in before_events] == [id_one, id_two]

        between_events = event_log_storage.get_asset_events(
            AssetKey("asset_1"),
            include_cursor=True,
            before_cursor=id_three,
            after_cursor=id_one,
            ascending=True,
        )
        assert len(between_events) == 1
        assert [id for id, event in between_events] == [id_two]


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
        assert asset_key.to_string() == '["path", "to", "asset_4"]'
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


def test_asset_key_structure():
    src_dir = file_relative_path(__file__, "compat_tests/snapshot_0_9_16_asset_key_structure")
    with copy_directory(src_dir) as test_dir:
        asset_storage = ConsolidatedSqliteEventLogStorage(test_dir)
        asset_keys = asset_storage.get_all_asset_keys()
        assert len(asset_keys) == 5

        # get a structured asset key
        asset_key = AssetKey(["dashboards", "cost_dashboard"])

        # check that backcompat events are read
        assert asset_storage.has_asset_key(asset_key)
        events = asset_storage.get_asset_events(asset_key)
        assert len(events) == 1
        run_ids = asset_storage.get_asset_run_ids(asset_key)
        assert len(run_ids) == 1

        asset_storage.upgrade()

        # check that backcompat events are merged with newly stored events
        run_id = "fake_run_id"
        asset_storage.store_event(_materialization_event_record(run_id, asset_key))
        assert asset_storage.has_asset_key(asset_key)
        events = asset_storage.get_asset_events(asset_key)
        assert len(events) == 2
        run_ids = asset_storage.get_asset_run_ids(asset_key)
        assert len(run_ids) == 2


@asset_test
def test_asset_partition_query(asset_aware_context):
    with asset_aware_context() as ctx:
        instance, event_log_storage = ctx
        execute_partitioned_pipeline(instance, "partition_a")
        execute_partitioned_pipeline(instance, "partition_a")
        execute_partitioned_pipeline(instance, "partition_b")
        execute_partitioned_pipeline(instance, "partition_c")
        events = event_log_storage.get_asset_events(AssetKey("asset_key"))
        assert len(events) == 4

        events = event_log_storage.get_asset_events(
            AssetKey("asset_key"), partitions=["partition_a", "partition_b"]
        )
        assert len(events) == 3


def _materialization_event_record(run_id, asset_key):
    return DagsterEventRecord(
        None,
        "",
        "debug",
        "",
        run_id,
        time.time() - 25,
        step_key="my_step_key",
        pipeline_name="my_pipeline",
        dagster_event=DagsterEvent(
            DagsterEventType.STEP_MATERIALIZATION.value,
            "my_pipeline",
            step_key="my_step_key",
            event_specific_data=StepMaterializationData(AssetMaterialization(asset_key=asset_key)),
        ),
    )
