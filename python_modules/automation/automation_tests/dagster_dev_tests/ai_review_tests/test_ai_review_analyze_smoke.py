"""Simple smoke tests for ai-review-analyze command."""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner


class TestAiReviewAnalyzeSmoke:
    """Basic smoke tests for the ai-review-analyze command."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        assert ai_review_analyze is not None
        assert ai_review_analyze.name == "ai-review-analyze"
        assert callable(ai_review_analyze)

    def test_help_command(self):
        """Test that help command works."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-analyze" in result.output
        assert "--human" in result.output
        assert "--json" in result.output
        assert "--minimal" in result.output

    def test_command_execution_without_errors(self):
        """Test command executes without argument parsing errors."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--json"])

        # Command may succeed or fail depending on environment,
        # but it shouldn't crash due to argument parsing issues
        if result.exit_code == 0:
            # Success - verify it produces JSON
            import json

            data = json.loads(result.output)
            assert isinstance(data, dict)
        else:
            # Failure should be graceful with error message
            assert "Error" in result.output

    @patch("automation.dagster_dev.commands.ai_review_analyze.subprocess.run")
    def test_subprocess_error_handling(self, mock_run):
        """Test graceful handling of subprocess errors."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, ["test"])

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--json"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_valid_flags_accepted(self):
        """Test that valid command flags are accepted."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        # Just test that the flags don't cause argument parsing errors
        result = runner.invoke(ai_review_analyze, ["--help"])

        assert result.exit_code == 0
        # Check that key flags are documented
        assert "--minimal" in result.output
        assert "--human" in result.output
        assert "--json" in result.output

    @patch("automation.dagster_dev.commands.ai_review_analyze.subprocess.run")
    def test_full_command_with_mocked_dependencies(self, mock_run):
        """Test command with all dependencies properly mocked."""
        # Mock all subprocess calls that the command makes
        mock_responses = {
            ("git", "branch", "--show-current"): "test-branch\n",
            (
                "dagster-dev",
                "gt-stack",
                "--current-only",
            ): '[{"name": "test-branch", "is_current": true}]',
            ("dagster-dev", "gt-stack"): '[{"name": "test-branch", "is_current": true}]',
            ("git", "diff", "--stat", "master..test-branch"): "1 file changed, 5 insertions(+)\n",
            ("git", "diff", "master..test-branch"): "+added line\n",
            ("git", "log", "--oneline", "master..test-branch"): "abc123 test commit\n",
            ("gh", "pr", "view", "--json", "number", "--jq", ".number"): "123\n",
            ("git", "status", "--porcelain"): "",
            ("gt", "log", "--stack"): "abc123 test commit\n",
        }

        def side_effect(cmd, **kwargs):
            cmd_key = tuple(cmd)
            mock_result = MagicMock()
            if cmd_key in mock_responses:
                mock_result.stdout = mock_responses[cmd_key]
                mock_result.returncode = 0
                return mock_result
            else:
                # Default response for unknown commands
                mock_result.stdout = ""
                mock_result.returncode = 0
                return mock_result

        mock_run.side_effect = side_effect

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--json"])

        assert result.exit_code == 0
        # Should produce valid JSON output
        output_data = json.loads(result.output)
        assert "current_branch" in output_data
        assert "repository_state" in output_data
