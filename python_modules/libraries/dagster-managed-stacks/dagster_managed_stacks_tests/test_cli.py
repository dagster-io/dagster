import pytest
from click.testing import CliRunner
from dagster_managed_stacks import ManagedStackCheckResult, ManagedStackDiff, ManagedStackReconciler
from dagster_managed_stacks.cli import main

from dagster._utils import file_relative_path


@pytest.mark.parametrize(
    "command",
    ["check", "apply"],
)
def test_commands(command):

    runner = CliRunner()

    is_check = command == "check"

    check_result = runner.invoke(
        main,
        [command, file_relative_path(__file__, "./this_file_doesnt_exist.py")],
    )
    assert check_result.exit_code != 0

    check_result = runner.invoke(
        main, [command, file_relative_path(__file__, "./example_empty_module.py")]
    )
    assert check_result.exit_code == 0
    assert "Found 0 stacks" in check_result.output

    check_result = runner.invoke(
        main, [command, file_relative_path(__file__, "./example_module_in_sync_reconciler.py")]
    )
    assert check_result.exit_code == 0
    assert "Found 1 stacks" in check_result.output
    assert (
        "+" not in check_result.output
        and "-" not in check_result.output
        and "~" not in check_result.output
    ), check_result.output

    check_result = runner.invoke(
        main, [command, file_relative_path(__file__, "./example_module_out_of_sync_reconciler.py")]
    )
    assert check_result.exit_code == 0
    assert "Found 1 stacks" in check_result.output

    # Just make sure we see an addition or deletion in the output,
    # we don't really care about the contents, that's tested in the diff tests
    # This file has an addition in check and deletion in apply
    assert (
        ("+" in check_result.output) == is_check
        and ("-" in check_result.output) == (not is_check)
        and "~" not in check_result.output
    ), check_result.output

    check_result = runner.invoke(
        main,
        [command, file_relative_path(__file__, "./example_module_many_out_of_sync_reconcilers.py")],
    )
    assert check_result.exit_code == 0
    assert "Found 2 stacks" in check_result.output
    assert (
        "+" in check_result.output and "-" in check_result.output and "~" not in check_result.output
    ), check_result.output
