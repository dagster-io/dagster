import pytest
from click.testing import CliRunner
from dagster._utils import file_relative_path
from dagster_managed_elements.cli import main

TEST_ROOT_DIR = file_relative_path(__file__, ".")


@pytest.mark.parametrize(
    "command",
    ["check", "apply"],
)
def test_commands(command):
    runner = CliRunner()

    is_check = command == "check"

    check_result = runner.invoke(main, [command, "-m", "module_doesnt_exist", "-d", TEST_ROOT_DIR])
    assert check_result.exit_code != 0

    check_result = runner.invoke(main, [command, "-m", "example_empty_module", "-d", TEST_ROOT_DIR])
    assert check_result.exit_code == 0
    assert "Found 0 reconcilers" in check_result.output

    check_result = runner.invoke(
        main, [command, "-m", "example_module_in_sync_reconciler", "-d", TEST_ROOT_DIR]
    )
    assert check_result.exit_code == 0
    assert "Found 1 reconcilers" in check_result.output
    assert (
        "+ " not in check_result.output
        and "- " not in check_result.output
        and "~ " not in check_result.output
    ), check_result.output

    check_result = runner.invoke(
        main, [command, "-m", "example_module_out_of_sync_reconciler", "-d", TEST_ROOT_DIR]
    )
    assert check_result.exit_code == 0
    assert "Found 1 reconcilers" in check_result.output

    # Just make sure we see an addition or deletion in the output,
    # we don't really care about the contents, that's tested in the diff tests
    # This file has an addition in check and deletion in apply
    assert (
        ("+" in check_result.output) == is_check
        and ("-" in check_result.output) == (not is_check)
        and "~" not in check_result.output
    ), check_result.output

    check_result = runner.invoke(
        main, [command, "-m", "example_module_many_out_of_sync_reconcilers", "-d", TEST_ROOT_DIR]
    )
    assert check_result.exit_code == 0
    assert "Found 2 reconcilers" in check_result.output
    assert (
        "+ " in check_result.output
        and "- " in check_result.output
        and "~ " not in check_result.output
    ), check_result.output

    # Test specifying only a specific attr
    check_result = runner.invoke(
        main,
        [
            command,
            "-m",
            "example_module_many_out_of_sync_reconcilers:my_reconciler",
            "-d",
            TEST_ROOT_DIR,
        ],
    )
    assert check_result.exit_code == 0
    assert "Found 1 reconcilers" in check_result.output
    assert (
        "+" in check_result.output
        and "-" not in check_result.output
        and "~" not in check_result.output
    ), check_result.output

    # Test specifying both attrs
    check_result = runner.invoke(
        main,
        [
            command,
            "-m",
            "example_module_many_out_of_sync_reconcilers:my_other_reconciler,my_reconciler",
            "-d",
            TEST_ROOT_DIR,
        ],
    )
    assert check_result.exit_code == 0
    assert "Found 2 reconcilers" in check_result.output
    assert (
        "+ " in check_result.output
        and "- " in check_result.output
        and "~ " not in check_result.output
    ), check_result.output

    # Test specifying nested attr
    check_result = runner.invoke(
        main,
        [
            command,
            "-m",
            "example_module_many_out_of_sync_reconcilers:my_nested_reconciler.reconciler",
            "-d",
            TEST_ROOT_DIR,
        ],
    )
    assert check_result.exit_code == 0
    assert "Found 1 reconcilers" in check_result.output
    assert (
        "+ " not in check_result.output
        and "- " not in check_result.output
        and "~ " in check_result.output
    ), check_result.output
