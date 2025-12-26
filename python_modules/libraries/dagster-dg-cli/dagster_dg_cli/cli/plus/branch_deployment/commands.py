"""Commands for managing branch deployments in Dagster+."""

from pathlib import Path
from typing import Optional

import click
from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.git_utils import get_git_metadata_for_branch_deployment
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient
from dagster_dg_cli.utils.plus.gql_mutations import (
    create_or_update_branch_deployment,
    delete_branch_deployment,
)


def _get_organization(input_organization: Optional[str]) -> str:
    """Get organization from input or config.

    Args:
        input_organization: Organization from CLI flag (optional)

    Returns:
        Organization name

    Raises:
        click.UsageError: If organization not found
    """
    organization = input_organization
    if not organization:
        if not DagsterPlusCliConfig.exists():
            raise click.UsageError(
                "Organization not specified. To specify an organization, use the --organization option "
                "or run `dg plus login`."
            )
        plus_config = DagsterPlusCliConfig.get()
        organization = plus_config.organization

    if not organization:
        raise click.UsageError(
            "Organization not specified. To specify an organization, use the --organization option "
            "or run `dg plus login`."
        )
    return organization


@click.command(name="create-or-update", cls=DgClickCommand)
@click.option(
    "--organization",
    help="Dagster+ organization name. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_ORGANIZATION",
)
@click.option(
    "--read-git-state",
    is_flag=True,
    help="Read commit metadata (hash, timestamp, author, message) from git automatically.",
)
@click.option(
    "--commit-hash",
    help="Git commit hash. Required if --read-git-state is not used.",
)
@click.option(
    "--timestamp",
    type=float,
    help="Commit timestamp in Unix time (seconds since epoch). Required if --read-git-state is not used.",
)
@click.option(
    "--commit-message",
    help="Commit message for the latest commit.",
)
@click.option(
    "--author-name",
    help="Author name for the latest commit.",
)
@click.option(
    "--author-email",
    help="Author email for the latest commit.",
)
@click.option(
    "--author-avatar-url",
    help="URL for the avatar of the commit author.",
)
@click.option(
    "--branch-url",
    help="URL to the branch in version control.",
)
@click.option(
    "--pull-request-url",
    "--code-review-url",
    help="URL to the pull request or merge request for this branch.",
)
@click.option(
    "--pull-request-status",
    help="Status of the pull request (e.g., 'open', 'merged', 'closed').",
)
@click.option(
    "--pull-request-number",
    "--code-review-id",
    help="Pull request or merge request number/ID.",
)
@click.option(
    "--base-deployment-name",
    help="Name of the deployment to use as the base deployment for comparison.",
)
@click.option(
    "--snapshot-base-condition",
    type=click.Choice([c.value for c in SnapshotBaseDeploymentCondition]),
    help=(
        "When to snapshot the base deployment for highlighting changes:\n"
        "  - on-create: Snapshot when branch deployment is first created\n"
        "  - on-update: Update snapshot every time branch deployment is updated"
    ),
)
@dg_global_options
@cli_telemetry_wrapper
def create_or_update_command(
    organization: Optional[str],
    read_git_state: bool,
    commit_hash: Optional[str],
    timestamp: Optional[float],
    commit_message: Optional[str],
    author_name: Optional[str],
    author_email: Optional[str],
    author_avatar_url: Optional[str],
    branch_url: Optional[str],
    pull_request_url: Optional[str],
    pull_request_status: Optional[str],
    pull_request_number: Optional[str],
    base_deployment_name: Optional[str],
    snapshot_base_condition: Optional[str],
    **global_options: object,
) -> None:
    r"""Create or update a branch deployment with git metadata.

    This command creates or updates a branch deployment in Dagster+ with metadata
    about the current git state. Branch deployments are ephemeral environments for
    testing code changes before merging to production.

    The repository name and branch name are automatically detected from your git
    configuration. You can either use --read-git-state to automatically read commit
    metadata, or manually specify --commit-hash and --timestamp.

    Examples:
        # Create/update with auto-detected git metadata
        $ dg plus branch-deployment create-or-update --read-git-state

        # Create/update with manual commit info
        $ dg plus branch-deployment create-or-update \\
            --commit-hash abc123def456 \\
            --timestamp 1234567890

        # Include PR information
        $ dg plus branch-deployment create-or-update \\
            --read-git-state \\
            --pull-request-url https://github.com/org/repo/pull/123 \\
            --pull-request-number 123 \\
            --pull-request-status open
    """
    # Get organization (validates auth is configured)
    _get_organization(organization)

    # Get git metadata (repo name, branch name, and optionally commit metadata)
    _, repo_name, branch_name, git_commit_metadata = get_git_metadata_for_branch_deployment(
        Path.cwd(), read_git_state
    )

    # Validate commit info
    if read_git_state and git_commit_metadata:
        # Use git metadata
        final_commit_hash = str(git_commit_metadata["commit_hash"])
        final_timestamp = git_commit_metadata["timestamp"]
        # Use git metadata for author info if not explicitly provided
        if not commit_message:
            commit_message = git_commit_metadata.get("commit_message")  # type: ignore
        if not author_name:
            author_name = git_commit_metadata.get("author_name")  # type: ignore
        if not author_email:
            author_email = git_commit_metadata.get("author_email")  # type: ignore
    else:
        # Use manually provided values
        final_commit_hash = commit_hash
        final_timestamp = timestamp

    # Validate required fields
    if not final_commit_hash or final_timestamp is None:
        raise click.UsageError(
            "Must provide either --read-git-state flag, or both --commit-hash and --timestamp."
        )

    # Type narrowing - after validation we know these are not None
    assert isinstance(final_commit_hash, str)
    assert isinstance(final_timestamp, (int, float))

    # Convert snapshot_base_condition string to enum
    snapshot_enum = None
    if snapshot_base_condition:
        snapshot_enum = SnapshotBaseDeploymentCondition(snapshot_base_condition)

    # Create GraphQL client
    plus_config = (
        DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else DagsterPlusCliConfig()
    )
    client = DagsterPlusGraphQLClient.from_config(plus_config)

    # Call the mutation
    click.echo(f"Creating/updating branch deployment for {repo_name}:{branch_name}...")
    deployment_name = create_or_update_branch_deployment(
        client=client,
        repo_name=repo_name,
        branch_name=branch_name,
        commit_hash=final_commit_hash,
        timestamp=float(final_timestamp),
        commit_message=commit_message,
        author_name=author_name,
        author_email=author_email,
        author_avatar_url=author_avatar_url,
        branch_url=branch_url,
        pull_request_url=pull_request_url,
        pull_request_status=pull_request_status,
        pull_request_number=pull_request_number,
        base_deployment_name=base_deployment_name,
        snapshot_base_condition=snapshot_enum,
    )

    click.echo(f"✓ Branch deployment '{deployment_name}' created/updated successfully")


@click.command(name="delete", cls=DgClickCommand)
@click.argument("deployment", type=str)
@click.option(
    "--organization",
    help="Dagster+ organization name. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_ORGANIZATION",
)
@dg_global_options
@cli_telemetry_wrapper
def delete_command(
    deployment: str,
    organization: Optional[str],
    **global_options: object,
) -> None:
    """Delete a branch deployment by name.

    This command deletes a branch deployment from Dagster+. Only branch deployments
    can be deleted - you cannot delete full deployments or prod deployments with
    this command.

    Arguments:
        DEPLOYMENT: Name of the branch deployment to delete

    Examples:
        # Delete a branch deployment
        $ dg plus branch-deployment delete my-feature-branch

        # Delete with explicit organization
        $ dg plus branch-deployment delete my-feature-branch --organization myorg
    """
    # Get organization (this also validates we have auth configured)
    _get_organization(organization)

    # Create GraphQL client
    plus_config = (
        DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else DagsterPlusCliConfig()
    )
    client = DagsterPlusGraphQLClient.from_config(plus_config)

    # Delete the deployment
    click.echo(f"Deleting branch deployment '{deployment}'...")
    deployment_id = delete_branch_deployment(client, deployment)

    click.echo(f"✓ Branch deployment '{deployment}' (ID: {deployment_id}) deleted successfully")
