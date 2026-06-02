"""Scaffold a GitHub Actions workflow for `dg labs ai dispatch`."""

from pathlib import Path

import click
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand, exit_with_error
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.plus.deploy.configure.utils import search_for_git_root

_WORKFLOW_TEMPLATE = (
    Path(__file__).parent.parent.parent / "templates" / "dg-ai-dispatch-github-action.yaml"
)
_WORKFLOW_OUTPUT = Path(".github") / "workflows" / "dg-ai-dispatch.yml"


def _scaffold_github_actions_ai_dispatch(git_root: Path | None, force: bool) -> None:
    resolved_git_root = git_root or search_for_git_root(Path.cwd())
    if resolved_git_root is None:
        exit_with_error(
            "No git repository found. Must be run from a git repository, or specify the path "
            "to the git root with `--git-root`."
        )

    workflow_path = resolved_git_root / _WORKFLOW_OUTPUT
    if workflow_path.exists() and not force:
        raise click.ClickException(
            f"Workflow already exists at {workflow_path}. Use --force to overwrite it."
        )

    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(_WORKFLOW_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    click.echo(
        click.style(
            "GitHub Actions workflow for dg labs ai dispatch created successfully.", fg="green"
        )
    )
    click.echo(f"Created: {workflow_path}")
    click.echo(
        "Commit and push this file before running `dg labs ai dispatch` against the repository."
    )
    click.echo(
        "Before running the workflow, configure the ANTHROPIC_API_KEY GitHub Actions secret."
    )
    click.echo(
        "Optional: set the CLAUDE_ENABLED repository variable to false to disable dispatch runs."
    )


@click.command(
    name="github-actions-ai-dispatch",
    cls=DgClickCommand,
    hidden=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@click.option("--force", is_flag=True, help="Overwrite an existing workflow file")
@dg_global_options
@cli_telemetry_wrapper
def scaffold_github_actions_ai_dispatch_command(
    git_root: Path | None, force: bool, **global_options: object
) -> None:
    """Scaffold the GitHub Actions workflow required by `dg labs ai dispatch`."""
    _scaffold_github_actions_ai_dispatch(git_root=git_root, force=force)


@click.command(
    name="github-actions-ai-dispatch",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@click.option("--force", is_flag=True, help="Overwrite an existing workflow file")
@dg_global_options
@cli_telemetry_wrapper
def labs_scaffold_github_actions_ai_dispatch_command(
    git_root: Path | None, force: bool, **global_options: object
) -> None:
    """Scaffold the GitHub Actions workflow required by `dg labs ai dispatch`."""
    _scaffold_github_actions_ai_dispatch(git_root=git_root, force=force)
