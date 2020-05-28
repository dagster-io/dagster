from contextlib import contextmanager

import pytest

from dagster import (
    DagsterEventType,
    Materialization,
    Output,
    execute_pipeline,
    pipeline,
    seven,
    solid,
)
from dagster.core.events.log import EventRecord
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
)
from dagster.core.storage.local_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage


def get_instance(temp_dir, event_log_storage):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=event_log_storage,
        compute_log_manager=NoOpComputeLogManager(temp_dir),
        run_launcher=SyncInMemoryRunLauncher(),
    )


@contextmanager
def create_in_memory_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        yield get_instance(temp_dir, InMemoryEventLogStorage())


@contextmanager
def create_consolidated_sqlite_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        yield get_instance(temp_dir, ConsolidatedSqliteEventLogStorage(temp_dir))


asset_test = pytest.mark.parametrize(
    'asset_aware_instance',
    [create_in_memory_event_log_instance, create_consolidated_sqlite_event_log_instance,],
)


@solid
def solid_one(_):
    yield Materialization(label='one', asset_key='asset_1')
    yield Output(1)


@solid
def solid_two(_):
    yield Materialization(label='two', asset_key='asset_2')
    yield Materialization(label='three', asset_key='asset_3')
    yield Output(1)


@pipeline
def pipeline_one():
    solid_one()


@pipeline
def pipeline_two():
    solid_one()
    solid_two()


@asset_test
def test_asset_keys(asset_aware_instance):
    with asset_aware_instance() as instance:
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_keys = set(
            instance._event_storage.get_all_asset_keys()  # pylint: disable=protected-access
        )
        assert asset_keys == set(['asset_1', 'asset_2', 'asset_3'])


@asset_test
def test_asset_events(asset_aware_instance):
    with asset_aware_instance() as instance:
        execute_pipeline(pipeline_one, instance=instance)
        execute_pipeline(pipeline_two, instance=instance)
        asset_events = instance._event_storage.get_asset_events(  # pylint: disable=protected-access
            'asset_1'
        )
        assert len(asset_events) == 2
        for event in asset_events:
            assert isinstance(event, EventRecord)
            assert event.is_dagster_event
            assert event.dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION
            assert event.dagster_event.asset_key


@asset_test
def test_asset_run_ids(asset_aware_instance):
    with asset_aware_instance() as instance:
        one = execute_pipeline(pipeline_one, instance=instance)
        two = execute_pipeline(pipeline_two, instance=instance)
        run_ids = instance._event_storage.get_asset_run_ids(  # pylint: disable=protected-access
            'asset_1'
        )
        assert set(run_ids) == set([one.run_id, two.run_id])
