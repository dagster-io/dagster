import pytest
from click.testing import CliRunner

from dagster import AssetKey, Materialization, Output, execute_pipeline, pipeline, solid
from dagster.cli.asset import asset_wipe_command
from dagster.core.instance import DagsterInstance
from dagster.core.storage.event_log.base import AssetAwareEventLogStorage


@pytest.fixture(name="asset_instance")
def mock_asset_instance(mocker):
    # can use the ephemeral instance, since the default InMemoryEventLogStorage is asset aware
    instance = DagsterInstance.ephemeral()
    mocker.patch(
        'dagster.core.instance.DagsterInstance.get', return_value=instance,
    )
    yield instance


@solid
def solid_one(_):
    yield Materialization(label='one', asset_key=AssetKey('asset_1'))
    yield Output(1)


@solid
def solid_two(_):
    yield Materialization(label='two', asset_key=AssetKey('asset_2'))
    yield Materialization(label='three', asset_key=AssetKey(['path', 'to', 'asset_3']))
    yield Output(1)


@solid
def solid_normalization(_):
    yield Materialization(label='normalization', asset_key='path/to-asset_4')
    yield Output(1)


@pipeline
def pipeline_one():
    solid_one()


@pipeline
def pipeline_two():
    solid_one()
    solid_two()


def test_asset_wipe_errors():
    runner = CliRunner()
    result = runner.invoke(asset_wipe_command)
    assert result.exit_code == 2
    assert (
        'Error, you must specify an asset key or use `--all` to wipe all asset keys.'
        in result.output
    )

    result = runner.invoke(asset_wipe_command, ['--all', 'path.to.asset_key'])
    assert result.exit_code == 2
    assert 'Error, cannot use more than one of: asset key, `--all`.' in result.output


def test_asset_exit():
    runner = CliRunner()
    result = runner.invoke(asset_wipe_command, ['--all'], input='NOT_DELETE\n')
    assert result.exit_code == 0
    assert 'Exiting without removing asset indexes' in result.output


def test_asset_single_wipe(asset_instance):
    runner = CliRunner()
    execute_pipeline(pipeline_one, instance=asset_instance)
    execute_pipeline(pipeline_two, instance=asset_instance)
    event_log_storage = asset_instance._event_storage  # pylint: disable=protected-access
    assert isinstance(event_log_storage, AssetAwareEventLogStorage)
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 3

    result = runner.invoke(asset_wipe_command, ['path.to.asset_3'], input='DELETE\n')
    assert result.exit_code == 0
    assert 'Removed asset indexes from event logs' in result.output
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 2


def test_asset_multi_wipe(asset_instance):
    runner = CliRunner()
    execute_pipeline(pipeline_one, instance=asset_instance)
    execute_pipeline(pipeline_two, instance=asset_instance)
    event_log_storage = asset_instance._event_storage  # pylint: disable=protected-access
    assert isinstance(event_log_storage, AssetAwareEventLogStorage)
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 3

    result = runner.invoke(asset_wipe_command, ['path.to.asset_3', 'asset_1'], input='DELETE\n')
    assert result.exit_code == 0
    assert 'Removed asset indexes from event logs' in result.output
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 1


def test_asset_wipe_all(asset_instance):
    runner = CliRunner()
    execute_pipeline(pipeline_one, instance=asset_instance)
    execute_pipeline(pipeline_two, instance=asset_instance)
    event_log_storage = asset_instance._event_storage  # pylint: disable=protected-access
    assert isinstance(event_log_storage, AssetAwareEventLogStorage)
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 3

    result = runner.invoke(asset_wipe_command, ['--all'], input='DELETE\n')
    assert result.exit_code == 0
    assert 'Removed asset indexes from event logs' in result.output
    asset_keys = event_log_storage.get_all_asset_keys()
    assert len(asset_keys) == 0
