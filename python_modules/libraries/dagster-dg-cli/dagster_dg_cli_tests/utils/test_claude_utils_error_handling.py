"""Unit tests for error handling in claude_utils.py."""

from unittest.mock import Mock, patch

import pytest
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_cli.utils.claude_utils import run_claude


class TestRunClaudeErrorHandling:
    """Test error handling in run_claude function."""

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_claude_command_failure_with_stderr(self, mock_subprocess_run):
        """Test error handling when Claude command fails with stderr."""
        # Mock subprocess.run to return failure with stderr
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "some stdout"
        mock_result.stderr = "Authentication failed: Invalid API key"
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1", "tool2"]

        with pytest.raises(RuntimeError) as exc_info:
            run_claude(dg_context, prompt, allowed_tools)

        error_msg = str(exc_info.value)
        assert "Claude command failed with return code 1" in error_msg
        assert "Stderr: Authentication failed: Invalid API key" in error_msg
        assert "Stdout: some stdout" in error_msg

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_claude_command_failure_without_stderr(self, mock_subprocess_run):
        """Test error handling when Claude command fails without stderr."""
        # Mock subprocess.run to return failure without stderr
        mock_result = Mock()
        mock_result.returncode = 127
        mock_result.stdout = "command not found output"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1"]

        with pytest.raises(RuntimeError) as exc_info:
            run_claude(dg_context, prompt, allowed_tools)

        error_msg = str(exc_info.value)
        assert "Claude command failed with return code 127" in error_msg
        assert "Stdout: command not found output" in error_msg
        # Should not contain stderr section when empty
        assert "Stderr:" not in error_msg

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_claude_command_failure_no_output(self, mock_subprocess_run):
        """Test error handling when Claude command fails with no output."""
        # Mock subprocess.run to return failure with no output
        mock_result = Mock()
        mock_result.returncode = 2
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = []

        with pytest.raises(RuntimeError) as exc_info:
            run_claude(dg_context, prompt, allowed_tools)

        error_msg = str(exc_info.value)
        assert "Claude command failed with return code 2" in error_msg
        # Should not contain output sections when empty
        assert "Stderr:" not in error_msg
        assert "Stdout:" not in error_msg

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_empty_stdout_with_success_return_code(self, mock_subprocess_run):
        """Test error handling when Claude command succeeds but returns empty stdout."""
        # Mock subprocess.run to return success but empty stdout
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1"]

        with pytest.raises(RuntimeError) as exc_info:
            run_claude(dg_context, prompt, allowed_tools)

        error_msg = str(exc_info.value)
        assert "Claude command succeeded but returned empty output" in error_msg
        # Should not contain stderr section when empty
        assert "Stderr:" not in error_msg

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_empty_stdout_with_stderr(self, mock_subprocess_run):
        """Test error handling when Claude returns empty stdout but has stderr."""
        # Mock subprocess.run to return success but empty stdout with stderr
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = "Warning: some warning message"
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1", "tool2"]

        with pytest.raises(RuntimeError) as exc_info:
            run_claude(dg_context, prompt, allowed_tools)

        error_msg = str(exc_info.value)
        assert "Claude command succeeded but returned empty output" in error_msg
        assert "Stderr: Warning: some warning message" in error_msg

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_whitespace_only_stdout(self, mock_subprocess_run):
        """Test error handling when Claude returns only whitespace."""
        # Mock subprocess.run to return success but only whitespace
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "   \n\t   \n  "
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = []

        with pytest.raises(RuntimeError) as exc_info:
            run_claude(dg_context, prompt, allowed_tools)

        error_msg = str(exc_info.value)
        assert "Claude command succeeded but returned empty output" in error_msg

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_successful_claude_call(self, mock_subprocess_run):
        """Test successful Claude call returns stdout."""
        # Mock subprocess.run to return success with valid output
        expected_output = '{"branch-name": "test-branch", "pr-title": "Test PR"}'
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = expected_output
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1"]

        result = run_claude(dg_context, prompt, allowed_tools)

        assert result == expected_output

    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_successful_claude_call_with_stderr_warnings(self, mock_subprocess_run):
        """Test successful Claude call with stderr warnings still returns stdout."""
        # Mock subprocess.run to return success with warnings in stderr
        expected_output = "Valid Claude response"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = expected_output
        mock_result.stderr = "Warning: deprecated feature used"
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1", "tool2"]

        result = run_claude(dg_context, prompt, allowed_tools)

        # Should return stdout despite stderr warnings
        assert result == expected_output

    @patch("dagster_dg_cli.utils.claude_utils.find_claude")
    @patch("dagster_dg_cli.utils.claude_utils.subprocess.run")
    def test_command_construction_called_correctly(self, mock_subprocess_run, mock_find_claude):
        """Test that subprocess.run is called with correct parameters."""
        # Mock find_claude to return claude command
        mock_find_claude.return_value = ["claude"]

        # Mock subprocess.run to return success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        dg_context = Mock(spec=DgContext)
        prompt = "test prompt"
        allowed_tools = ["tool1", "tool2"]

        run_claude(dg_context, prompt, allowed_tools)

        # Verify subprocess.run was called correctly
        mock_subprocess_run.assert_called_once_with(
            ["claude", "-p", "test prompt", "--allowedTools", "tool1,tool2"],
            check=False,
            capture_output=True,
            text=True,
        )
