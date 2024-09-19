import tempfile

import pytest
from click.testing import CliRunner
from dagster import AssetKey, AssetMaterialization, Output, job, op
from dagster._cli.asset import asset_wipe_cache_command, asset_wipe_command
from dagster._core.storage.partition_status_cache import AssetStatusCacheValue
from dagster._core.test_utils import instance_for_test
from dagster._seven import json


@pytest.fixture(name="instance_runner")
def mock_instance_runner():
    with tempfile.TemporaryDirectory() as dagster_home_temp:
        with instance_for_test(
            temp_dir=dagster_home_temp,
        ) as instance:
            runner = CliRunner(env={"DAGSTER_HOME": dagster_home_temp})
            yield instance, runner


@op
def op_one(_):
    yield AssetMaterialization(asset_key=AssetKey("asset_1"))
    yield Output(1)


@op
def op_two(_):
    yield AssetMaterialization(asset_key=AssetKey("asset_2"))
    yield AssetMaterialization(asset_key=AssetKey(["path", "to", "asset_3"]))
    yield AssetMaterialization(asset_key=AssetKey(("path", "to", "asset_4")))
    yield Output(1)


@op
def op_normalization(_):
    yield AssetMaterialization(asset_key="path/to-asset_5")
    yield Output(1)


@job
def job_one():
    op_one()


@job
def job_two():
    op_one()
    op_two()


@pytest.mark.parametrize("command", [asset_wipe_command, asset_wipe_cache_command])
def test_asset_wipe_errors(instance_runner, command):
    _, runner = instance_runner
    result = runner.invoke(command)
    assert result.exit_code == 2
    assert "Error, you must specify an asset key or use `--all`" in result.output

    result = runner.invoke(command, ["--all", json.dumps(["path", "to", "asset_key"])])
    assert result.exit_code == 2
    assert "Error, cannot use more than one of: asset key, `--all`." in result.output


@pytest.mark.parametrize(
    "command, message",
    [
        (asset_wipe_command, "Exiting without removing asset indexes"),
        (asset_wipe_cache_command, "Exiting without wiping the partitions status cache"),
    ],
)
def test_asset_exit(instance_runner, command, message):
    _, runner = instance_runner
    result = runner.invoke(command, ["--all"], input="NOT_DELETE\n")
    assert result.exit_code == 0
    assert message in result.output


def test_asset_single_wipe(instance_runner):
    instance, runner = instance_runner
    job_one.execute_in_process(instance=instance)
    job_two.execute_in_process(instance=instance)
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 4

    result = runner.invoke(
        asset_wipe_command, [json.dumps(["path", "to", "asset_3"])], input="DELETE\n"
    )
    assert result.exit_code == 0
    assert "Removed asset indexes from event logs" in result.output

    result = runner.invoke(
        asset_wipe_command, [json.dumps(["path", "to", "asset_4"])], input="DELETE\n"
    )
    assert result.exit_code == 0
    assert "Removed asset indexes from event logs" in result.output

    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 2


def test_asset_multi_wipe(instance_runner):
    instance, runner = instance_runner
    job_one.execute_in_process(instance=instance)
    job_two.execute_in_process(instance=instance)
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 4

    result = runner.invoke(
        asset_wipe_command,
        [json.dumps(["path", "to", "asset_3"]), json.dumps(["asset_1"])],
        input="DELETE\n",
    )
    assert result.exit_code == 0
    assert "Removed asset indexes from event logs" in result.output
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 2


def test_asset_wipe_all(instance_runner):
    instance, runner = instance_runner
    job_one.execute_in_process(instance=instance)
    job_two.execute_in_process(instance=instance)
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 4

    result = runner.invoke(asset_wipe_command, ["--all"], input="DELETE\n")
    assert result.exit_code == 0
    assert "Removed asset indexes from event logs" in result.output
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 0


def test_asset_single_wipe_noprompt(instance_runner):
    instance, runner = instance_runner
    job_one.execute_in_process(instance=instance)
    job_two.execute_in_process(instance=instance)
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 4

    result = runner.invoke(
        asset_wipe_command, ["--noprompt", json.dumps(["path", "to", "asset_3"])]
    )
    assert result.exit_code == 0
    assert "Removed asset indexes from event logs" in result.output

    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 3


def _get_cached_status_for_asset(instance, asset_key):
    asset_records = list(instance.get_asset_records([asset_key]))
    assert len(asset_records) == 1
    return asset_records[0].asset_entry.cached_status


def test_asset_single_wipe_cache(instance_runner):
    instance, runner = instance_runner
    job_one.execute_in_process(instance=instance)
    job_two.execute_in_process(instance=instance)
    asset_1 = AssetKey("asset_1")
    asset_2 = AssetKey("asset_2")

    dummy_cache_value = AssetStatusCacheValue(1, "foo", "bar")
    for key in [asset_1, asset_2]:
        instance.update_asset_cached_status_data(key, dummy_cache_value)
        assert _get_cached_status_for_asset(instance, key) == dummy_cache_value

    result = runner.invoke(asset_wipe_cache_command, [json.dumps(asset_1.path)], input="DELETE\n")
    assert result.exit_code == 0
    assert "Cleared the partitions status cache" in result.output

    assert _get_cached_status_for_asset(instance, asset_1) is None
    assert _get_cached_status_for_asset(instance, asset_2) == dummy_cache_value


def test_asset_multi_wipe_cache(instance_runner):
    instance, runner = instance_runner
    job_one.execute_in_process(instance=instance)
    job_two.execute_in_process(instance=instance)
    asset_1 = AssetKey("asset_1")
    asset_2 = AssetKey("asset_2")
    asset_3 = AssetKey(["path", "to", "asset_3"])

    dummy_cache_value = AssetStatusCacheValue(1, "foo", "bar")
    for key in [asset_1, asset_2, asset_3]:
        instance.update_asset_cached_status_data(key, dummy_cache_value)
        assert _get_cached_status_for_asset(instance, key) == dummy_cache_value

    result = runner.invoke(
        asset_wipe_cache_command,
        [json.dumps(asset_3.path), json.dumps(asset_1.path)],
        input="DELETE\n",
    )
    assert result.exit_code == 0
    assert "Cleared the partitions status cache" in result.output

    for key in [asset_1, asset_3]:
        assert _get_cached_status_for_asset(instance, key) is None
    assert _get_cached_status_for_asset(instance, asset_2) == dummy_cache_value


def test_asset_wipe_all_cache_status_values(instance_runner):
    instance, runner = instance_runner
    job_two.execute_in_process(instance=instance)
    asset_2 = AssetKey("asset_2")
    asset_3 = AssetKey(["path", "to", "asset_3"])

    dummy_cache_value = AssetStatusCacheValue(1, "foo", "bar")
    for key in [asset_2, asset_3]:
        instance.update_asset_cached_status_data(key, dummy_cache_value)
        assert _get_cached_status_for_asset(instance, key) == dummy_cache_value

    result = runner.invoke(asset_wipe_cache_command, ["--all"], input="DELETE\n")
    assert result.exit_code == 0
    assert "Cleared the partitions status cache" in result.output

    records = list(instance.get_asset_records())
    for record in records:
        assert record.asset_entry.cached_status is None
