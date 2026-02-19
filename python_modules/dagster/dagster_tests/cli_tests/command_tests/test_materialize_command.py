import dagster as dg
from click.testing import CliRunner
from dagster._cli.asset import asset_materialize_command


def invoke_materialize(
    select: str,
    partition: str | None = None,
    partition_range: str | None = None,
):
    runner = CliRunner()
    options = ["-f", dg.file_relative_path(__file__, "assets.py"), "--select", select]
    if partition:
        options.extend(["--partition", partition])
    if partition_range:
        options.extend(["--partition-range", partition_range])
    return runner.invoke(asset_materialize_command, options)


def test_empty():
    with dg.instance_for_test():
        runner = CliRunner()

        result = runner.invoke(asset_materialize_command, [])
        assert result.exit_code == 2
        assert "Missing option '--select'" in result.output


def test_missing_origin():
    with dg.instance_for_test():
        runner = CliRunner()

        result = runner.invoke(asset_materialize_command, ["--select", "asset1"])
        assert result.exit_code == 2
        assert "Invalid set of CLI arguments for loading repository/job" in result.output


def test_single_asset():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("asset1")
        assert "RUN_SUCCESS" in result.output
        assert instance.get_latest_materialization_event(dg.AssetKey("asset1")) is not None
        assert result.exit_code == 0


def test_multi_segment_asset_key():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("some/key/prefix/asset_with_prefix")

        assert "RUN_SUCCESS" in result.output
        assert (
            instance.get_latest_materialization_event(
                dg.AssetKey(["some", "key", "prefix", "asset_with_prefix"])
            )
            is not None
        )


def test_asset_with_dep():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("downstream_asset")
        assert "RUN_SUCCESS" in result.output
        assert instance.get_latest_materialization_event(dg.AssetKey("asset1")) is None
        assert (
            instance.get_latest_materialization_event(dg.AssetKey("downstream_asset")) is not None
        )


def test_two_assets():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("asset1,downstream_asset")
        assert "RUN_SUCCESS" in result.output
        for asset_key in [dg.AssetKey("asset1"), dg.AssetKey("downstream_asset")]:
            assert instance.get_latest_materialization_event(asset_key) is not None


def test_all_downstream():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("asset1*")
        assert "RUN_SUCCESS" in result.output
        for asset_key in [dg.AssetKey("asset1"), dg.AssetKey("downstream_asset")]:
            assert instance.get_latest_materialization_event(asset_key) is not None


def test_all_upstream():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("*downstream_asset")
        assert "RUN_SUCCESS" in result.output
        for asset_key in [dg.AssetKey("asset1"), dg.AssetKey("downstream_asset")]:
            assert instance.get_latest_materialization_event(asset_key) is not None


def test_partition():
    with dg.instance_for_test() as instance:
        result = invoke_materialize("partitioned_asset", "one")
        assert "RUN_SUCCESS" in result.output
        event = instance.get_latest_materialization_event(dg.AssetKey("partitioned_asset"))
        assert event is not None
        assert event.asset_materialization.partition == "one"  # pyright: ignore[reportOptionalMemberAccess]


def test_partition_option_with_non_partitioned_asset():
    with dg.instance_for_test():
        result = invoke_materialize("asset1", "one")
        assert "Provided '--partition' option, but none of the assets are partitioned" in str(
            result.exception
        )


def test_no_partition_option_with_partitioned_asset():
    with dg.instance_for_test():
        result = invoke_materialize("partitioned_asset")
        assert "Asset has partitions, but no '--partition' option was provided" in str(
            result.exception
        )


def test_asset_key_missing():
    with dg.instance_for_test():
        result = invoke_materialize("nonexistent_asset")
        assert "no AssetsDefinition objects supply these keys" in str(result.exception)


def test_one_of_the_asset_keys_missing():
    with dg.instance_for_test():
        result = invoke_materialize("asset1,nonexistent_asset")
        assert "no AssetsDefinition objects supply these keys" in str(result.exception)


def test_conflicting_partitions():
    with dg.instance_for_test():
        result = invoke_materialize("partitioned_asset,differently_partitioned_asset", "one")
        assert "There is no PartitionsDefinition shared by all the provided assets" in str(
            result.exception
        )


def test_partition_and_partition_range_options():
    with dg.instance_for_test():
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
    with dg.instance_for_test():
        result = invoke_materialize(
            "single_run_partitioned_asset",
            partition_range="2020-01-01",
        )
        assert "Invalid partition range format. Expected <start>...<end>." in str(result.exception)


def test_partition_range_single_run_backfill_policy():
    """Test that partition range works for assets with single_run backfill policy.

    The partition range is executed in a single run using partition range tags,
    not by creating a backfill.
    """
    with dg.instance_for_test() as instance:
        result = invoke_materialize(
            "single_run_partitioned_asset",
            partition_range="2020-01-01...2020-01-03",
        )
        assert result.exit_code == 0
        assert "RUN_SUCCESS" in result.output

        backfills = instance.get_backfills()
        assert len(backfills) == 0

        runs = instance.get_runs()
        assert len(runs) == 1


def test_partition_range_multi_run_backfill_policy():
    """Test that partition range fails for assets with multi_run backfill policy.

    Assets with multi_run backfill policy cannot use partition ranges in the CLI
    because they would require creating a backfill with separate runs per partition,
    which needs a running daemon process.
    """
    with dg.instance_for_test():
        result = invoke_materialize(
            "multi_run_partitioned_asset",
            partition_range="2020-01-01...2020-01-03",
        )
        assert result.exit_code != 0
        assert "Partition ranges with the CLI require all selected assets to have a" in str(
            result.exception
        )
        assert "BackfillPolicy.single_run()" in str(result.exception)


def test_partition_range_no_backfill_policy():
    """Test that partition range fails for assets without a backfill policy.

    This is the correct fix for issue #31055. Assets without a backfill policy
    cannot use partition ranges in the CLI because they would require creating
    a backfill with separate runs per partition, which needs a running daemon process.
    The CLI validation now properly catches this case.
    """
    with dg.instance_for_test():
        result = invoke_materialize(
            "partitioned_asset",
            partition_range="one...three",
        )
        assert result.exit_code != 0
        assert "Partition ranges with the CLI require all selected assets to have a" in str(
            result.exception
        )
        assert "BackfillPolicy.single_run()" in str(result.exception)


def test_failure():
    result = invoke_materialize("fail_asset")
    assert result.exit_code == 1


def test_run_cli_config_json():
    with dg.instance_for_test() as instance:
        asset_key = "asset_assert_with_config"
        runner = CliRunner()
        options = [
            "-f",
            dg.file_relative_path(__file__, "assets.py"),
            "--select",
            asset_key,
            "--config-json",
            '{"ops": {"asset_assert_with_config": {"config": {"some_prop": "foo"}}}}',
        ]

        result = runner.invoke(asset_materialize_command, options)
        assert not isinstance(result, dg.DagsterInvalidConfigError)
        assert instance.get_latest_materialization_event(dg.AssetKey(asset_key)) is not None
        assert result.exit_code == 0
