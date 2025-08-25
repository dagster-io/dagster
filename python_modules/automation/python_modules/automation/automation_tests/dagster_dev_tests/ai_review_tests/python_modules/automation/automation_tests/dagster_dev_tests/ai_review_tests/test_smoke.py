"""Single smoke test file for ai-review command family."""

from click.testing import CliRunner


class TestAiReviewSmoke:
    """Basic smoke tests for all ai-review commands."""

    def test_cache_import(self):
        """Test ai-review-cache import."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        assert ai_review_cache is not None
        assert ai_review_cache.name == "ai-review-cache"

    def test_cache_help(self):
        """Test ai-review-cache help."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--help"])
        assert result.exit_code == 0

    def test_summarize_import(self):
        """Test ai-review-summarize import."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        assert ai_review_summarize is not None
        assert ai_review_summarize.name == "ai-review-summarize"

    def test_summarize_help(self):
        """Test ai-review-summarize help."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--help"])
        assert result.exit_code == 0

    def test_analyze_import(self):
        """Test ai-review-analyze import."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        assert ai_review_analyze is not None
        assert ai_review_analyze.name == "ai-review-analyze"

    def test_analyze_help(self):
        """Test ai-review-analyze help."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--help"])
        assert result.exit_code == 0

    def test_update_import(self):
        """Test ai-review-update import."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        assert update_pr is not None
        assert update_pr.name == "ai-review-update"

    def test_update_help(self):
        """Test ai-review-update help."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        runner = CliRunner()
        result = runner.invoke(update_pr, ["--help"])
        assert result.exit_code == 0

    def test_update_required_params(self):
        """Test ai-review-update requires title and body."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        runner = CliRunner()
        result = runner.invoke(update_pr, ["--body", "test"])
        assert result.exit_code != 0
        assert "Missing option '--title'" in result.output
