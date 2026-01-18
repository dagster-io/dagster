"""Simple smoke tests for ai-review-cache command."""

from unittest.mock import Mock, patch

from click.testing import CliRunner


class TestAiReviewCacheSmoke:
    """Basic smoke tests for the ai-review-cache command."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        assert ai_review_cache is not None
        assert ai_review_cache.name == "ai-review-cache"
        assert callable(ai_review_cache)

    def test_help_command(self):
        """Test that help command works."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-cache" in result.output
        assert "--action" in result.output
        assert "--format" in result.output

    def test_status_with_no_cache(self):
        """Test status command when cache doesn't exist."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": False,
                "size_bytes": 0,
                "entries": 0,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "No cache found" in result.output

    def test_status_json_format(self):
        """Test status command with JSON output."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": False,
                "size_bytes": 0,
                "entries": 0,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status", "--format", "json"])

            assert result.exit_code == 0
            assert "exists" in result.output

    def test_clear_command(self):
        """Test cache clear command."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.clear_cache.return_value = True
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "clear"])

            assert result.exit_code == 0
            mock_instance.clear_cache.assert_called_once()

    def test_invalid_action(self):
        """Test command with invalid action."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--action", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_invalid_format(self):
        """Test command with invalid format."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--format", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output
