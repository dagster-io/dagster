"""Integration tests for update-pr-and-commit command."""

import subprocess
from unittest.mock import Mock, patch

from click.testing import CliRunner


def create_mock_subprocess_result(returncode=0, stdout="", stderr=""):
    """Create a mock subprocess.CompletedProcess result."""
    result = Mock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestUpdatePrAndCommit:
    """Test cases for the update-pr-and-commit command."""

    def test_successful_pr_and_commit_update(self):
        """Test successful PR and commit update."""

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run calls for different commands."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                return create_mock_subprocess_result(stdout="12345")
            elif cmd == ["gh", "pr", "edit", "--title", "Fix important bug"]:
                return create_mock_subprocess_result()
            elif cmd == [
                "gh",
                "pr",
                "edit",
                "--body",
                "This fixes the critical issue with user authentication",
            ]:
                return create_mock_subprocess_result()
            elif cmd == [
                "git",
                "commit",
                "--amend",
                "-m",
                "Fix important bug\n\nThis fixes the critical issue with user authentication",
            ]:
                return create_mock_subprocess_result()
            else:
                return create_mock_subprocess_result(returncode=1)

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(
                update_pr,
                [
                    "--title",
                    "Fix important bug",
                    "--body",
                    "This fixes the critical issue with user authentication",
                ],
            )

            assert result.exit_code == 0
            assert "🔄 Updating PR and commit message..." in result.output
            assert "1️⃣ Verifying PR exists..." in result.output
            assert "✅ Found PR #12345" in result.output
            assert "2️⃣ Updating PR title..." in result.output
            assert "✅ PR title updated: Fix important bug" in result.output
            assert "3️⃣ Updating PR body..." in result.output
            assert "✅ PR body updated" in result.output
            assert "4️⃣ Updating commit message..." in result.output
            assert "✅ Commit message updated: Fix important bug" in result.output
            assert "🎉 Successfully updated PR #12345!" in result.output
            assert (
                "🔗 Graphite PR View: https://app.graphite.dev/github/pr/dagster-io/dagster/12345/"
                in result.output
            )

    def test_successful_pr_update_with_custom_commit_title(self):
        """Test PR update with custom commit title."""

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run calls."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                return create_mock_subprocess_result(stdout="54321")
            elif cmd == ["gh", "pr", "edit", "--title", "Add new feature"]:
                return create_mock_subprocess_result()
            elif cmd == ["gh", "pr", "edit", "--body", "This adds support for feature X"]:
                return create_mock_subprocess_result()
            elif cmd == [
                "git",
                "commit",
                "--amend",
                "-m",
                "feat: Custom commit title\n\nThis adds support for feature X",
            ]:
                return create_mock_subprocess_result()
            else:
                return create_mock_subprocess_result(returncode=1)

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(
                update_pr,
                [
                    "--title",
                    "Add new feature",
                    "--body",
                    "This adds support for feature X",
                    "--commit-title",
                    "feat: Custom commit title",
                ],
            )

            assert result.exit_code == 0
            assert "✅ Commit message updated: feat: Custom commit title" in result.output

    def test_no_pr_found_error(self):
        """Test error when no PR is found for current branch."""

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run to simulate no PR found."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                # Simulate subprocess.CalledProcessError
                raise subprocess.CalledProcessError(1, cmd, "", "")
            else:
                return create_mock_subprocess_result()

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(update_pr, ["--title", "Test title", "--body", "Test body"])

            assert result.exit_code == 1
            # The actual error message comes from run_command(), not the exception handler
            assert "Error getting PR number" in result.output

    def test_pr_title_update_failure(self):
        """Test failure when updating PR title."""

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run with PR title update failure."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                return create_mock_subprocess_result(stdout="12345")
            elif cmd == ["gh", "pr", "edit", "--title", "Test title"]:
                raise subprocess.CalledProcessError(1, cmd, "", "Permission denied")
            else:
                return create_mock_subprocess_result()

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(update_pr, ["--title", "Test title", "--body", "Test body"])

            assert result.exit_code == 1
            assert "Error updating PR title" in result.output
            assert "stderr: Permission denied" in result.output

    def test_pr_body_update_failure(self):
        """Test failure when updating PR body."""

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run with PR body update failure."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                return create_mock_subprocess_result(stdout="12345")
            elif cmd == ["gh", "pr", "edit", "--title", "Test title"]:
                return create_mock_subprocess_result()
            elif cmd == ["gh", "pr", "edit", "--body", "Test body"]:
                raise subprocess.CalledProcessError(1, cmd, "", "Network error")
            else:
                return create_mock_subprocess_result()

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(update_pr, ["--title", "Test title", "--body", "Test body"])

            assert result.exit_code == 1
            assert "Error updating PR body" in result.output

    def test_git_commit_amend_failure(self):
        """Test failure when amending git commit."""

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run with git commit failure."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                return create_mock_subprocess_result(stdout="12345")
            elif cmd == ["gh", "pr", "edit", "--title", "Test title"]:
                return create_mock_subprocess_result()
            elif cmd == ["gh", "pr", "edit", "--body", "Test body"]:
                return create_mock_subprocess_result()
            elif cmd == ["git", "commit", "--amend", "-m", "Test title\n\nTest body"]:
                raise subprocess.CalledProcessError(1, cmd, "nothing to commit", "")
            else:
                return create_mock_subprocess_result()

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(update_pr, ["--title", "Test title", "--body", "Test body"])

            assert result.exit_code == 1
            assert "Error updating commit message" in result.output
            assert "stdout: nothing to commit" in result.output

    def test_multiline_pr_body(self):
        """Test PR update with multiline body."""
        multiline_body = "This is a detailed description.\n\nIt has multiple paragraphs.\n\n- Feature A\n- Feature B"

        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run calls."""
            cmd = args[0] if args else kwargs.get("args", [])

            if cmd == ["gh", "pr", "view", "--json", "number", "--jq", ".number"]:
                return create_mock_subprocess_result(stdout="12345")
            elif cmd == ["gh", "pr", "edit", "--title", "Multiline test"]:
                return create_mock_subprocess_result()
            elif cmd == ["gh", "pr", "edit", "--body", multiline_body]:
                return create_mock_subprocess_result()
            elif cmd == ["git", "commit", "--amend", "-m", f"Multiline test\n\n{multiline_body}"]:
                return create_mock_subprocess_result()
            else:
                return create_mock_subprocess_result(returncode=1)

        with patch(
            "automation.dagster_dev.commands.update_pr_and_commit.subprocess.run",
            side_effect=mock_subprocess_run,
        ):
            from automation.dagster_dev.commands.update_pr_and_commit import update_pr

            runner = CliRunner()
            result = runner.invoke(
                update_pr, ["--title", "Multiline test", "--body", multiline_body]
            )

            assert result.exit_code == 0
            assert "✅ PR body updated" in result.output
            assert "✅ Commit message updated: Multiline test" in result.output

    def test_required_arguments(self):
        """Test that title and body arguments are required."""
        from automation.dagster_dev.commands.update_pr_and_commit import update_pr

        runner = CliRunner()

        # Test missing title
        result = runner.invoke(update_pr, ["--body", "Test body"])
        assert result.exit_code != 0
        assert "Missing option '--title'" in result.output

        # Test missing body
        result = runner.invoke(update_pr, ["--title", "Test title"])
        assert result.exit_code != 0
        assert "Missing option '--body'" in result.output

        # Test missing both
        result = runner.invoke(update_pr, [])
        assert result.exit_code != 0
        assert "Missing option" in result.output
