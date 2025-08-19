"""Integration tests for bk-latest-build-for-pr command."""

import json
from unittest.mock import Mock, patch

from click.testing import CliRunner


def test_bk_latest_build_for_pr_integration():
    """Integration test against real PR 31774 which should return build 131689."""
    # Mock the subprocess calls to simulate PR 31774 with build 131689
    pr_view_response = json.dumps({"number": 31774})

    # Mock PR checks response for PR 31774
    buildkite_check = {
        "name": "buildkite/dagster-oss-main",
        "state": "SUCCESS",
        "link": "https://buildkite.com/dagster/dagster-oss-main/builds/131689",
    }
    pr_checks_response = json.dumps([buildkite_check])

    def mock_subprocess_run(*args, **kwargs):
        """Mock subprocess.run to return expected responses."""
        cmd = args[0]

        if cmd == ["gh", "pr", "view", "--json", "number"]:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = pr_view_response
            return mock_result
        elif cmd == ["gh", "pr", "checks", "--json", "name,state,link"]:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = pr_checks_response
            return mock_result

        # Default mock for unexpected calls
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        return mock_result

    with patch(
        "automation.dagster_dev.commands.bk_latest_build_for_pr.subprocess.run",
        side_effect=mock_subprocess_run,
    ):
        from automation.dagster_dev.commands.bk_latest_build_for_pr import bk_latest_build_for_pr

        # Use Click's test runner
        runner = CliRunner()
        result = runner.invoke(bk_latest_build_for_pr, [])

        # Verify success and output
        assert result.exit_code == 0
        assert result.output.strip() == "131689"


def test_bk_latest_build_for_pr_no_pr():
    """Test error handling when no PR is found."""

    def mock_subprocess_run(*args, **kwargs):
        """Mock subprocess.run to simulate no PR found."""
        cmd = args[0]

        if cmd == ["gh", "pr", "view", "--json", "number"]:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            return mock_result

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        return mock_result

    with patch(
        "automation.dagster_dev.commands.bk_latest_build_for_pr.subprocess.run",
        side_effect=mock_subprocess_run,
    ):
        from automation.dagster_dev.commands.bk_latest_build_for_pr import bk_latest_build_for_pr

        # Use Click's test runner
        runner = CliRunner()
        result = runner.invoke(bk_latest_build_for_pr, [])

        # Verify error exit and message
        assert result.exit_code == 1
        assert "Error: No PR found for current branch" in result.output


def test_bk_latest_build_for_pr_no_buildkite_checks():
    """Test error handling when no Buildkite checks are found."""
    pr_view_response = json.dumps({"number": 12345})
    # Mock PR checks response without Buildkite checks
    non_buildkite_check = {
        "name": "github-actions/test",
        "state": "SUCCESS",
        "link": "https://github.com/dagster-io/dagster/actions/runs/12345",
    }
    pr_checks_response = json.dumps([non_buildkite_check])

    def mock_subprocess_run(*args, **kwargs):
        """Mock subprocess.run to return non-Buildkite checks."""
        cmd = args[0]

        if cmd == ["gh", "pr", "view", "--json", "number"]:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = pr_view_response
            return mock_result
        elif cmd == ["gh", "pr", "checks", "--json", "name,state,link"]:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = pr_checks_response
            return mock_result

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        return mock_result

    with patch(
        "automation.dagster_dev.commands.bk_latest_build_for_pr.subprocess.run",
        side_effect=mock_subprocess_run,
    ):
        from automation.dagster_dev.commands.bk_latest_build_for_pr import bk_latest_build_for_pr

        # Use Click's test runner
        runner = CliRunner()
        result = runner.invoke(bk_latest_build_for_pr, [])

        # Verify error exit and message
        assert result.exit_code == 1
        assert "Error: No Buildkite checks found for current PR" in result.output
