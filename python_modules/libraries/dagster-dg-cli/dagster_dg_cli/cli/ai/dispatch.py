import os
import re
import subprocess
import time
from datetime import datetime
from typing import TYPE_CHECKING

import click
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_rest_resources.api.issue import DgApiIssueApi
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import (
    DEPLOYMENT_OPTION,
    ORGANIZATION_OPTION,
    TOKEN_OPTION,
    VIEW_GRAPHQL_OPTION,
    get_deployment,
    get_organization,
    get_user_token,
)

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.utils.github import (
    GitHubError,
    get_authenticated_github_user_login,
    get_github_repository,
    parse_github_remote_url,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.issue import DgApiIssue
    from githubkit.versions.latest.models import PullRequest


_DISPATCH_WORKFLOW_FILE = "dg-ai-dispatch.yml"
_DISPATCH_LABEL = "dagster-agent-dispatch"


class DispatchError(Exception):
    """Base class for user-facing AI dispatch errors."""


class CommandError(DispatchError):
    """Raised when an external command used by dispatch fails."""


@click.command(name="dispatch", cls=DgClickCommand)
@click.argument("issue_id", type=int)
@click.option(
    "--repo", "target_repo", type=str, default=None, help="GitHub repository (owner/repo)."
)
@click.option("--model", type=str, default=None, hidden=True)
@click.option("--plan-only", is_flag=True, default=False, hidden=True)
@VIEW_GRAPHQL_OPTION
@TOKEN_OPTION
@ORGANIZATION_OPTION
@DEPLOYMENT_OPTION
@cli_telemetry_wrapper
@click.pass_context
def dispatch_command(
    ctx: click.Context,
    issue_id: int,
    target_repo: str | None,
    model: str | None,
    plan_only: bool,
    deployment: str | None,
    organization: str | None,
    api_token: str | None,
    view_graphql: bool,
) -> None:
    """Dispatch an autonomous AI workflow from a Dagster issue.

    Example:
      dg labs ai dispatch 7
    """
    try:
        _dispatch_command_impl(
            ctx=ctx,
            issue_id=issue_id,
            target_repo=target_repo,
            model=model,
            plan_only=plan_only,
            deployment=deployment,
            organization=organization,
            api_token=api_token,
            view_graphql=view_graphql,
        )
    except (DispatchError, GitHubError) as exc:
        raise click.ClickException(str(exc)) from exc


def _dispatch_command_impl(
    *,
    ctx: click.Context,
    issue_id: int,
    target_repo: str | None,
    model: str | None,
    plan_only: bool,
    deployment: str | None,
    organization: str | None,
    api_token: str | None,
    view_graphql: bool,
) -> None:
    owner, repo = _resolve_repo_slug(target_repo)
    github_repo = get_github_repository(owner, repo).get_repository()
    default_branch = github_repo.default_branch
    _ensure_dispatch_workflow_exists(owner, repo)
    issue = _get_issue_from_context(
        ctx=ctx,
        issue_id=issue_id,
        organization=organization,
        deployment=deployment,
        api_token=api_token,
        view_graphql=view_graphql,
    )
    prompt = _format_issue_context(issue)
    submitted_by = get_authenticated_github_user_login()
    branch_name = _generate_branch_name(issue.title)

    branch_name = _create_branch_and_prompt_commit(
        owner=owner,
        repo=repo,
        default_branch=default_branch,
        branch_name=branch_name,
        prompt=prompt,
    )
    pull_request = _create_draft_pr(
        owner=owner,
        repo=repo,
        default_branch=default_branch,
        branch_name=branch_name,
        prompt=prompt,
    )

    distinct_id = f"{int(time.time()):x}"
    _dispatch_workflow(
        owner=owner,
        repo=repo,
        branch_name=branch_name,
        pr_number=pull_request.number,
        submitted_by=submitted_by,
        distinct_id=distinct_id,
        model=model,
        plan_only=plan_only,
    )

    click.echo(click.style("Dispatched AI workflow.", fg="green"))
    click.echo(f"Repository: {owner}/{repo}")
    click.echo(f"Branch: {branch_name}")
    click.echo(f"PR: {pull_request.html_url}")
    click.echo("GitHub Action: triggered")
    click.echo(
        f"Workflow: {_get_repo_url(owner, repo, github_repo.html_url)}/actions/workflows/{_DISPATCH_WORKFLOW_FILE}?query=branch%3A{branch_name}"
    )


def _run_command(args: list[str]) -> str:
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise CommandError(f"Command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        output = exc.stderr.strip() or exc.stdout.strip()
        command = " ".join(args)
        if output:
            raise CommandError(f"{output}\n(command: {command})") from exc
        raise CommandError(f"Command failed: {command}") from exc
    return result.stdout.strip()


def _resolve_repo_slug(target_repo: str | None) -> tuple[str, str]:
    if target_repo is not None:
        parts = target_repo.split("/")
        if len(parts) != 2 or not all(parts):
            raise DispatchError("--repo must be in owner/repo format.")
        return parts[0], parts[1]

    remote_url = _run_command(["git", "remote", "get-url", "origin"])
    parsed = parse_github_remote_url(remote_url)
    if parsed is None:
        raise DispatchError(
            "Could not infer GitHub repo from git remote 'origin'. Pass --repo owner/repo."
        )
    return parsed


def _ensure_dispatch_workflow_exists(owner: str, repo: str) -> None:
    repository = get_github_repository(owner, repo)
    if repository.workflow_exists(_DISPATCH_WORKFLOW_FILE):
        return

    raise DispatchError(
        f"Workflow '{_DISPATCH_WORKFLOW_FILE}' was not found (or is not accessible) in {owner}/{repo}. "
        "Run `dg labs scaffold github-actions-ai-dispatch` in that repository and commit the generated workflow, "
        "or pass --repo owner/repo if this repo is wrong."
    )


def _get_issue_from_context(
    *,
    ctx: click.Context,
    issue_id: int,
    organization: str | None,
    deployment: str | None,
    api_token: str | None,
    view_graphql: bool,
) -> "DgApiIssue":
    resolved_organization = organization or get_organization(ctx)
    if not resolved_organization:
        raise click.UsageError(
            "A Dagster Cloud organization must be specified when dispatching from an issue ID.\n\n"
            "You may specify an organization by:\n"
            "- Providing the --organization parameter\n"
            "- Setting the DAGSTER_CLOUD_ORGANIZATION environment variable"
        )

    resolved_deployment = deployment or get_deployment(ctx)
    if not resolved_deployment:
        raise click.UsageError(
            "A Dagster Cloud deployment must be specified when dispatching from an issue ID.\n\n"
            "You may specify a deployment by:\n"
            "- Providing the --deployment parameter\n"
            "- Setting the DAGSTER_CLOUD_DEPLOYMENT environment variable"
        )

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=resolved_deployment,
        organization=resolved_organization,
        user_token=api_token or get_user_token(ctx),
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)

    return DgApiIssueApi(client).get_issue(str(issue_id))


def _format_issue_context(issue: "DgApiIssue") -> str:
    return (
        "Address this Dagster issue. Here is the issue payload:\n\n"
        "```json\n"
        f"{issue.model_dump_json(indent=2, exclude_none=True)}\n"
        "```"
    )


def _generate_branch_name(source_text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", source_text.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if not slug:
        slug = "task"
    slug = slug[:48].rstrip("-")
    date_prefix = datetime.now().strftime("%m-%d")
    return f"{date_prefix}-{slug}"


def _get_repo_url(owner: str, repo: str, repo_url: str | None) -> str:
    if repo_url:
        return repo_url.rstrip("/")

    server_url = os.getenv("GITHUB_SERVER_URL")
    if server_url:
        return f"{server_url.rstrip('/')}/{owner}/{repo}"

    return f"https://github.com/{owner}/{repo}"


def _create_branch_and_prompt_commit(
    *,
    owner: str,
    repo: str,
    default_branch: str,
    branch_name: str,
    prompt: str,
) -> str:
    repository = get_github_repository(owner, repo)
    sha = repository.get_branch_sha(default_branch)
    if not sha:
        raise DispatchError("Could not resolve default branch SHA.")

    chosen_branch = branch_name
    if repository.branch_exists(chosen_branch):
        suffix = f"{time.time_ns():x}"[-6:]
        chosen_branch = f"{branch_name}-{suffix}"

    repository.create_branch(chosen_branch, sha)

    commit_message = f"Dispatch: {prompt}"
    repository.create_file(
        ".dg/ai-dispatch/prompt.md",
        commit_message,
        f"{prompt}\n".encode(),
        chosen_branch,
    )
    return chosen_branch


def _create_draft_pr(
    *,
    owner: str,
    repo: str,
    default_branch: str,
    branch_name: str,
    prompt: str,
) -> "PullRequest":
    max_title_len = 60
    suffix = "..." if len(prompt) > max_title_len else ""
    title = f"Dispatch: {prompt[:max_title_len]}{suffix}"
    body = f"_Dispatch: plan content will be populated by the AI dispatch workflow._\n\n**Prompt:** {prompt}"
    repository = get_github_repository(owner, repo)
    pull_request = repository.create_pull_request(
        title=title,
        head=branch_name,
        base=default_branch,
        body=body,
        draft=True,
    )
    repository.add_labels(pull_request.number, [_DISPATCH_LABEL])
    return pull_request


def _dispatch_workflow(
    *,
    owner: str,
    repo: str,
    branch_name: str,
    pr_number: int,
    submitted_by: str,
    distinct_id: str,
    model: str | None,
    plan_only: bool,
) -> None:
    repository = get_github_repository(owner, repo)
    inputs: dict[str, str] = {
        "branch_name": branch_name,
        "pr_number": str(pr_number),
        "submitted_by": submitted_by,
        "distinct_id": distinct_id,
    }
    if model:
        inputs["model_name"] = model
    if plan_only:
        inputs["plan_only"] = "true"

    repository.dispatch_workflow(_DISPATCH_WORKFLOW_FILE, branch_name, inputs)
