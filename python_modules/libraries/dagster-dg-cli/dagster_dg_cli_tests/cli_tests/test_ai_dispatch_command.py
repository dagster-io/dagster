import re
import subprocess
from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner
from dagster_dg_cli.cli.ai import ai_group
from dagster_dg_cli.cli.ai.dispatch import (
    _create_branch_and_prompt_commit,
    _create_draft_pr,
    _dispatch_workflow,
    _format_issue_context,
    _generate_branch_name,
    _get_repo_url,
)
from dagster_dg_cli.cli.scaffold.github_actions_ai_dispatch import (
    labs_scaffold_github_actions_ai_dispatch_command,
)
from dagster_dg_cli.utils.github import parse_github_remote_url
from dagster_rest_resources.__generated__.enums import IssueStatus
from dagster_rest_resources.schemas.issue import DgApiIssue
from dagster_test.dg_utils.utils import ProxyRunner, assert_runner_result


def test_ai_group_not_visible_in_top_level_help() -> None:
    with ProxyRunner.test() as runner:
        result = runner.invoke("--help")
        assert_runner_result(result)
        assert " ai " not in result.output
        assert " labs " in result.output


def test_labs_ai_subcommands_visible_in_help() -> None:
    with ProxyRunner.test() as runner:
        result = runner.invoke("labs", "ai", "--help")
        assert_runner_result(result)
        assert " dispatch " in result.output


def test_parse_github_remote_url(monkeypatch) -> None:
    assert parse_github_remote_url("git@github.com:dagster-io/dagster.git") == (
        "dagster-io",
        "dagster",
    )
    assert parse_github_remote_url("https://github.com/dagster-io/dagster") == (
        "dagster-io",
        "dagster",
    )

    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.example.com")
    assert parse_github_remote_url("git@github.example.com:dagster-io/dagster.git") == (
        "dagster-io",
        "dagster",
    )
    assert parse_github_remote_url("https://github.example.com/dagster-io/dagster") == (
        "dagster-io",
        "dagster",
    )
    assert parse_github_remote_url("not-a-github-url") is None


def test_get_repo_url(monkeypatch) -> None:
    assert (
        _get_repo_url(
            "dagster-io",
            "dagster",
            "https://github.example.com/dagster-io/dagster",
        )
        == "https://github.example.com/dagster-io/dagster"
    )

    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.example.com")
    assert (
        _get_repo_url("dagster-io", "dagster", None)
        == "https://github.example.com/dagster-io/dagster"
    )


def test_format_issue_context() -> None:
    issue = DgApiIssue(
        id="7",
        title="Broken deployment",
        description="Investigate the rollout failure.",
        status=IssueStatus.OPEN,
        created_by_name="octocat",
        linked_objects=[],
        context="Recent changes touched the Kubernetes manifests.",
    )

    assert _format_issue_context(issue) == (
        "Address this Dagster issue. Here is the issue payload:\n\n"
        "```json\n"
        "{\n"
        '  "id": "7",\n'
        '  "title": "Broken deployment",\n'
        '  "description": "Investigate the rollout failure.",\n'
        '  "status": "OPEN",\n'
        '  "created_by_name": "octocat",\n'
        '  "linked_objects": [],\n'
        '  "context": "Recent changes touched the Kubernetes manifests."\n'
        "}\n"
        "```"
    )


def test_generate_branch_name() -> None:
    branch_name = _generate_branch_name("Fix flaky test in scheduler!!!")
    assert re.fullmatch(r"\d{2}-\d{2}-fix-flaky-test-in-scheduler", branch_name)


def test_create_branch_and_prompt_commit_retries_with_time_ns_suffix(monkeypatch) -> None:
    repository = Mock()
    repository.get_branch_sha.return_value = "abc123"
    repository.branch_exists.return_value = True

    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch.get_github_repository", lambda owner, repo: repository
    )
    monkeypatch.setattr("dagster_dg_cli.cli.ai.dispatch.time.time_ns", lambda: 1234567890123456789)

    branch_name = _create_branch_and_prompt_commit(
        owner="dagster-io",
        repo="dagster",
        default_branch="main",
        branch_name="dispatch-branch",
        prompt="Fix flaky test",
    )

    assert branch_name == "dispatch-branch-e98115"
    repository.create_branch.assert_called_once_with("dispatch-branch-e98115", "abc123")
    repository.create_file.assert_called_once_with(
        ".dg/ai-dispatch/prompt.md",
        "Dispatch: Fix flaky test",
        b"Fix flaky test\n",
        "dispatch-branch-e98115",
    )


def test_create_draft_pr_adds_dispatch_label(monkeypatch) -> None:
    repository = Mock()
    pull_request = Mock()
    pull_request.number = 123
    pull_request.html_url = "https://github.com/dagster-io/dagster/pull/123"
    repository.create_pull_request.return_value = pull_request

    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch.get_github_repository", lambda owner, repo: repository
    )

    created_pull_request = _create_draft_pr(
        owner="dagster-io",
        repo="dagster",
        default_branch="main",
        branch_name="dispatch-branch",
        prompt="Fix flaky test",
    )

    assert created_pull_request == pull_request
    repository.create_pull_request.assert_called_once_with(
        title="Dispatch: Fix flaky test",
        head="dispatch-branch",
        base="main",
        body="_Dispatch: plan content will be populated by the AI dispatch workflow._\n\n**Prompt:** Fix flaky test",
        draft=True,
    )
    repository.add_labels.assert_called_once_with(123, ["dagster-agent-dispatch"])


def test_dispatch_requires_issue_id() -> None:
    result = CliRunner().invoke(ai_group, ["dispatch"])

    assert result.exit_code != 0
    assert "Missing argument 'ISSUE_ID'" in result.output


def test_dispatch_workflow_uses_committed_prompt_file(monkeypatch) -> None:
    repository = Mock()
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch.get_github_repository", lambda owner, repo: repository
    )

    _dispatch_workflow(
        owner="dagster-io",
        repo="dagster",
        branch_name="dispatch-branch",
        pr_number=123,
        submitted_by="octocat",
        distinct_id="abc123",
        model="claude-opus-4-6",
        plan_only=True,
    )

    repository.dispatch_workflow.assert_called_once_with(
        "dg-ai-dispatch.yml",
        "dispatch-branch",
        {
            "branch_name": "dispatch-branch",
            "pr_number": "123",
            "submitted_by": "octocat",
            "distinct_id": "abc123",
            "model_name": "claude-opus-4-6",
            "plan_only": "true",
        },
    )


def test_dispatch_accepts_integer_issue_ids(monkeypatch) -> None:
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._resolve_repo_slug", lambda repo: ("dagster-io", "dagster")
    )
    repository = Mock()
    github_repo = Mock()
    github_repo.default_branch = "main"
    github_repo.html_url = "https://github.example.com/dagster-io/dagster"
    repository.get_repository.return_value = github_repo
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch.get_github_repository", lambda owner, repo: repository
    )
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._ensure_dispatch_workflow_exists",
        lambda owner, repo: None,
    )
    issue = Mock()
    issue.title = "Issue title"
    issue.model_dump_json.return_value = "Issue context"
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._get_issue_from_context",
        lambda **kwargs: issue,
    )
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch.get_authenticated_github_user_login", lambda: "octocat"
    )
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._generate_branch_name", lambda prompt: "dispatch-branch"
    )
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._create_branch_and_prompt_commit",
        lambda owner, repo, default_branch, branch_name, prompt: branch_name,
    )
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._create_draft_pr",
        lambda owner, repo, default_branch, branch_name, prompt: Mock(
            number=123,
            html_url="https://github.com/dagster-io/dagster/pull/123",
        ),
    )
    monkeypatch.setattr(
        "dagster_dg_cli.cli.ai.dispatch._dispatch_workflow",
        lambda **kwargs: None,
    )

    result = CliRunner().invoke(
        ai_group,
        [
            "dispatch",
            "7",
            "--organization",
            "test-org",
            "--deployment",
            "test-deployment",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Dispatched AI workflow." in result.output
    assert (
        "Workflow: https://github.example.com/dagster-io/dagster/actions/workflows/dg-ai-dispatch.yml?query=branch%3Adispatch-branch"
        in result.output
    )


def test_scaffold_github_actions_ai_dispatch_creates_workflow() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        subprocess.run(["git", "init"], check=True, capture_output=True)

        result = runner.invoke(labs_scaffold_github_actions_ai_dispatch_command)

        assert result.exit_code == 0, result.output
        workflow_path = Path(".github/workflows/dg-ai-dispatch.yml")
        assert workflow_path.exists()
        workflow_text = workflow_path.read_text(encoding="utf-8")
        assert "name: dg-ai-dispatch" in workflow_text
        assert "anthropics/claude-code-action@v1" in workflow_text
        assert "--permission-mode auto" in workflow_text
        assert "--dangerously-skip-permissions" not in workflow_text
        assert (
            "prompt:"
            not in workflow_text.split("workflow_dispatch:", maxsplit=1)[1].split(
                "concurrency:", maxsplit=1
            )[0]
        )
        assert "Commit plan to branch" not in workflow_text
        assert "ANTHROPIC_API_KEY GitHub Actions secret" in result.output


def test_scaffold_github_actions_ai_dispatch_refuses_to_overwrite() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        subprocess.run(["git", "init"], check=True, capture_output=True)
        workflow_path = Path(".github/workflows/dg-ai-dispatch.yml")
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text("existing workflow\n", encoding="utf-8")

        result = runner.invoke(labs_scaffold_github_actions_ai_dispatch_command)

        assert result.exit_code != 0
        assert "Workflow already exists" in result.output
        assert workflow_path.read_text(encoding="utf-8") == "existing workflow\n"
