from typing import Optional

from click.testing import CliRunner
from dagster._cli.asset import asset_list_command
from dagster._utils import file_relative_path


def invoke_list(select: Optional[str] = None, partition: Optional[str] = None):
    runner = CliRunner()
    options = ["-f", file_relative_path(__file__, "assets.py")]
    if select:
        options.extend(["--select", select])
    return runner.invoke(asset_list_command, options)


def test_empty():
    runner = CliRunner()

    result = runner.invoke(asset_list_command, [])
    assert result.exit_code == 2
    assert "Must specify a python file or module name" in result.output


def test_no_selection():
    result = invoke_list()
    assert (
        result.output
        == "\n".join(
            [
                "asset1",
                "differently_partitioned_asset",
                "downstream_asset",
                "fail_asset",
                "multi_run_partitioned_asset",
                "partitioned_asset",
                "single_run_partitioned_asset",
                "some/key/prefix/asset_with_prefix",
            ]
        )
        + "\n"
    )


def test_single_asset():
    result = invoke_list("asset1")
    assert result.output == "asset1\n"


def test_multi_segment_asset_key():
    result = invoke_list("some/key/prefix/asset_with_prefix")
    assert result.output == "some/key/prefix/asset_with_prefix\n"


def test_two_assets():
    result = invoke_list("asset1,downstream_asset")
    assert result.output == "asset1\ndownstream_asset\n"


def test_all_downstream():
    result = invoke_list("asset1*")
    assert result.output == "asset1\ndownstream_asset\n"


def test_asset_key_missing():
    result = invoke_list("nonexistent_asset")
    assert result.output == ""
    assert result.exception is None


def test_one_of_the_asset_keys_missing():
    result = invoke_list("asset1,nonexistent_asset")
    assert result.output == "asset1\n"
    assert result.exception is None
