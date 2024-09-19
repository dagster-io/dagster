from typing import Optional

from click.testing import CliRunner
from dagster import AssetKey
from dagster._cli.asset import asset_materialize_command
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path


def invoke_materialize(
    select: str,
    partition: Optional[str] = None,
    partition_range: Optional[str] = None,
):
    runner = CliRunner()
    options = ["-f", file_relative_path(__file__, "assets.py"), "--select", select]
    if partition:
        options.extend(["--partition", partition])
    if partition_range:
        options.extend(["--partition-range", partition_range])
    return runner.invoke(asset_materialize_command, options)


def test_empty():
    with instance_for_test():
        runner = CliRunner()

        result = runner.invoke(asset_materialize_command, [])
        assert result.exit_code == 2
        assert "Missing option '--select'" in result.output


def test_missing_origin():
    with instance_for_test():
        runner = CliRunner()

        result = runner.invoke(asset_materialize_command, ["--select", "asset1"])
        assert result.exit_code == 2
        assert "Must specify a python file or module name" in result.output


def test_single_asset():
    with instance_for_test() as instance:
        result = invoke_materialize("asset1")
        assert "RUN_SUCCESS" in result.output
        assert instance.get_latest_materialization_event(AssetKey("asset1")) is not None
        assert result.exit_code == 0


def test_multi_segment_asset_key():
    with instance_for_test() as instance:
        result = invoke_materialize("some/key/prefix/asset_with_prefix")

        assert "RUN_SUCCESS" in result.output
        assert (
            instance.get_latest_materialization_event(
                AssetKey(["some", "key", "prefix", "asset_with_prefix"])
            )
            is not None
        )


def test_asset_with_dep():
    with instance_for_test() as instance:
        result = invoke_materialize("downstream_asset")
        assert "RUN_SUCCESS" in result.output
        assert instance.get_latest_materialization_event(AssetKey("downstream_asset")) is not None


def test_two_assets():
    with instance_for_test() as instance:
        result = invoke_materialize("asset1,downstream_asset")
        assert "RUN_SUCCESS" in result.output
        for asset_key in [AssetKey("asset1"), AssetKey("downstream_asset")]:
            assert instance.get_latest_materialization_event(asset_key) is not None


def test_all_downstream():
    with instance_for_test() as instance:
        result = invoke_materialize("asset1*")
        assert "RUN_SUCCESS" in result.output
        for asset_key in [AssetKey("asset1"), AssetKey("downstream_asset")]:
            assert instance.get_latest_materialization_event(asset_key) is not None


def test_partition():
    with instance_for_test() as instance:
        result = invoke_materialize("partitioned_asset", "one")
        assert "RUN_SUCCESS" in result.output
        event = instance.get_latest_materialization_event(AssetKey("partitioned_asset"))
        assert event is not None
        assert event.asset_materialization.partition == "one"


def test_partition_option_with_non_partitioned_asset():
    with instance_for_test():
        result = invoke_materialize("asset1", "one")
        assert "Provided '--partition' option, but none of the assets are partitioned" in str(
            result.exception
        )


def test_no_partition_option_with_partitioned_asset():
    with instance_for_test():
        result = invoke_materialize("partitioned_asset")
        assert "Asset has partitions, but no '--partition' option was provided" in str(
            result.exception
        )


def test_asset_key_missing():
    with instance_for_test():
        result = invoke_materialize("nonexistent_asset")
        assert "no AssetsDefinition objects supply these keys" in str(result.exception)


def test_one_of_the_asset_keys_missing():
    with instance_for_test():
        result = invoke_materialize("asset1,nonexistent_asset")
        assert "no AssetsDefinition objects supply these keys" in str(result.exception)


def test_conflicting_partitions():
    with instance_for_test():
        result = invoke_materialize("partitioned_asset,differently_partitioned_asset", "one")
        assert "There is no PartitionsDefinition shared by all the provided assets" in str(
            result.exception
        )


def test_partition_and_partition_range_options():
    with instance_for_test():
        result = invoke_materialize(
            "single_run_partitioned_asset",
            partition="2020-01-01",
            partition_range="2020-01-01...2020-01-03",
        )
        assert (
            "Cannot specify both --partition and --partition-range options. Use only one."
            in str(result.exception)
        )


def test_partition_range_invalid_format():
    with instance_for_test():
        result = invoke_materialize(
            "single_run_partitioned_asset",
            partition_range="2020-01-01",
        )
        assert "Invalid partition range format. Expected <start>...<end>." in str(result.exception)


def test_partition_range_single_run_backfill_policy():
    with instance_for_test() as instance:
        result = invoke_materialize(
            "single_run_partitioned_asset",
            partition_range="2020-01-01...2020-01-03",
        )
        assert "RUN_SUCCESS" in result.output
        partitions = instance.get_materialized_partitions(AssetKey("single_run_partitioned_asset"))
        for partition in ["2020-01-01", "2020-01-02", "2020-01-03"]:
            assert partition in partitions


def test_partition_range_multi_run_backfill_policy():
    with instance_for_test():
        result = invoke_materialize(
            "multi_run_partitioned_asset",
            partition_range="2020-01-01...2020-01-03",
        )
        assert (
            "Provided partition range, but not all assets have a single-run backfill policy."
            in str(result.exception)
        )


def test_failure():
    result = invoke_materialize("fail_asset")
    assert result.exit_code == 1
