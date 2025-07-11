from unittest.mock import patch

import pytest
from dagster_dg_core.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()
from dagster_dg_core_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)


@pytest.fixture(scope="session")
def runner():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        yield runner


def test_ai_command_claude_not_installed(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = runner.invoke("ai")
        assert_runner_result(result, exit_0=False)
        assert "No supported CLI agent found" in result.output


def test_ai_command_keyboard_interrupt(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = KeyboardInterrupt()
        result = runner.invoke("ai")
        assert_runner_result(result, exit_0=False)


def test_ai_command_success(runner):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None  # Successful execution
        result = runner.invoke("ai", input="claude")
        assert_runner_result(result)
