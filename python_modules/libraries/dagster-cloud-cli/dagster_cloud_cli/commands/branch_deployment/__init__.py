import subprocess
from typing import Optional

import typer
from typer import Typer

from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition

from ... import gql, ui
from ...config_utils import dagster_cloud_options

app = Typer(help="Manage branch deployments for your organization.")

# https://git-scm.com/docs/git-log#Documentation/git-log.txt-emHem
HASH_PLACEHOLDER = "%H"
AUTHOR_EMAIL_PLACEHOLDER = "%ae"
AUTHOR_NAME_PLACEHOLDER = "%an"
TIMESTAMP_PLACEHOLDER = "%cd"
COMMIT_MESSAGE_PLACEHOLDER = "%s"

NEWLINE_PLACEHOLDER = "%n"

FORMAT_STRING = (
    f"{HASH_PLACEHOLDER}{NEWLINE_PLACEHOLDER}{AUTHOR_EMAIL_PLACEHOLDER}{NEWLINE_PLACEHOLDER}"
    f"{AUTHOR_NAME_PLACEHOLDER}{NEWLINE_PLACEHOLDER}{TIMESTAMP_PLACEHOLDER}{NEWLINE_PLACEHOLDER}{COMMIT_MESSAGE_PLACEHOLDER}"
)


def _read_git_state() -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", f"--format={FORMAT_STRING}", "--date=unix"]
        ).decode("utf-8")
    except subprocess.CalledProcessError:
        raise ui.error(
            "Could not read git state, ensure you are in a valid git repository if passing"
            " `--read-git-state`."
        )


@app.command(name="create-or-update")
@dagster_cloud_options(allow_empty=True)
def create_or_update(
    organization: str,
    api_token: str,
    url: str = typer.Option(
        None,
        "--url",
        help=(
            "[DEPRECATED] Your Dagster Cloud url, in the form of"
            " 'https://{ORGANIZATION_NAME}.dagster.cloud'."
        ),
        hidden=True,
    ),
    repo_name: str = typer.Option(
        ..., "--git-repo-name", "--repo-name", help="The name of the git repository."
    ),
    branch_name: str = typer.Option(
        ..., "--branch-name", help="The name of the version control branch."
    ),
    commit_hash: str = typer.Option(None, help="The latest commit hash."),
    timestamp: float = typer.Option(
        None, help="The latest commit timestamp, in unix time (seconds since epoch)."
    ),
    branch_url: str = typer.Option(None, help="The URL of the version control branch."),
    pull_request_url: str = typer.Option(
        None,
        "--code-review-url",
        "--pull-request-url",
        help="The URL to review this code, e.g. a Pull Request or Merge Request.",
    ),
    pull_request_status: str = typer.Option(None, help="The status of the pull request"),
    pull_request_number: str = typer.Option(
        None,
        "--code-review-id",
        "--pull-request-id",
        help="An identifier for the code review for this branch, e.g. a Pull Request number.",
    ),
    commit_message: str = typer.Option(None, help="The commit message for the latest commit."),
    author_name: str = typer.Option(None, help="The author name for the latest commit."),
    author_email: str = typer.Option(None, help="The author email for the latest commit."),
    author_avatar_url: str = typer.Option(
        None, help="The URL for the avatar of the author for the latest commit, if any."
    ),
    read_git_state: bool = typer.Option(
        False,
        is_flag=True,
        help="Whether to commit data (timestamp, hash, author info) from Git state.",
    ),
    base_deployment_name: str = typer.Option(
        None,
        help="The name of the deployment to use as the base deployment for the branch deployment.",
    ),
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition] = typer.Option(
        None,
        help="""
If and when to snapshot the definitions in the base deployment for highlighting changes in the branch:

\b
* None (default): No snapshots, branch is always compared to the live base deployment.
* on-create: Compare against a snapshot of the base deployment taken when the branch is first created.
* on-update: Compare against a snapshot that is updated every time the branch deployment is updated.
""",
        show_default=False,
    ),
) -> None:
    """Sets up or updates the branch deployment for the given git branch."""
    if not url and not organization:
        raise ui.error("Must provide either organization name or URL.")
    if not url:
        url = gql.url_from_config(organization=organization)

    if read_git_state:
        # Prints the following, separated by newlines:
        # full commit hash, author email, author name, timestamp, message
        git_out = _read_git_state()

        commit_hash, author_email, author_name, timestamp_str, commit_message = git_out.split(
            "\n", 4
        )
        timestamp = float(timestamp_str)

    if not commit_hash or not timestamp:
        raise ui.error(
            "Must provide `--commit-hash` and `--timestamp` parameters, or pass `--read-git-state`"
            " flag."
        )

    with gql.graphql_client_from_url(url, api_token) as client:
        ui.print(
            gql.create_or_update_branch_deployment(
                client,
                repo_name=repo_name,
                branch_name=branch_name,
                commit_hash=commit_hash,
                timestamp=timestamp,
                branch_url=branch_url,
                pull_request_url=pull_request_url,
                pull_request_status=pull_request_status,
                pull_request_number=pull_request_number,
                commit_message=commit_message,
                author_name=author_name,
                author_email=author_email,
                author_avatar_url=author_avatar_url,
                base_deployment_name=base_deployment_name,
                snapshot_base_condition=snapshot_base_condition,
            )
        )


@app.command(name="delete")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def delete(url: str, api_token: str, deployment: str):
    """Allows deletion of a branch deployment by name."""
    with gql.graphql_client_from_url(url, api_token) as client:
        gql.delete_branch_deployment(client, deployment=deployment)
