"""Simple smoke tests for ai-review-update command."""

from click.testing import CliRunner


class TestAiReviewUpdate:
    """Basic smoke tests for the ai-review-update command."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        assert update_pr is not None
        assert update_pr.name == "ai-review-update"
        assert callable(update_pr)

    def test_help_command(self):
        """Test that help command works."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        runner = CliRunner()
        result = runner.invoke(update_pr, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-update" in result.output
        assert "--title" in result.output
        assert "--body" in result.output

    def test_required_parameters(self):
        """Test that title and body arguments are required."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        runner = CliRunner()

        # Test missing title
        result = runner.invoke(update_pr, ["--body", "Test body"])
        assert result.exit_code != 0
        assert "Missing option '--title'" in result.output

        # Test missing body
        result = runner.invoke(update_pr, ["--title", "Test title"])
        assert result.exit_code != 0
        assert "Missing option '--body'" in result.output
