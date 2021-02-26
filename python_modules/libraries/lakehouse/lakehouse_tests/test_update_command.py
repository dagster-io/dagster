from click.testing import CliRunner
from dagster.core.test_utils import instance_for_test
from lakehouse.cli import update_cli
from lakehouse.errors import LakehouseLoadingError


def test_module_with_no_lakehouse():
    runner = CliRunner()

    with instance_for_test():
        result = runner.invoke(
            update_cli,
            ["--module", "lakehouse_tests.module_with_no_lakehouse"],
        )

    assert result.exit_code != 0
    assert isinstance(result.exception, LakehouseLoadingError)


def test_basic():
    runner = CliRunner()

    with instance_for_test():
        result = runner.invoke(
            update_cli,
            [
                "--module",
                "lakehouse_tests.lakehouse_for_tests",
                "--mode",
                "dev",
                "--assets",
                "asset1",
            ],
        )

    assert result.exit_code == 0


def test_bad_asset_query():
    runner = CliRunner()

    with instance_for_test():
        result = runner.invoke(
            update_cli,
            [
                "--module",
                "lakehouse_tests.lakehouse_for_tests",
                "--mode",
                "dev",
                "--assets",
                "asset1fds",
            ],
        )

    assert result.exit_code != 0
