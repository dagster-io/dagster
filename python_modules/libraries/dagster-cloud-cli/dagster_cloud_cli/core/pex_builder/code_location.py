import logging
import re
import subprocess
import time
from typing import Optional

from dagster_cloud_cli import gql
from dagster_cloud_cli.core.pex_builder import github_context
from dagster_cloud_cli.core.pex_builder.github_context import get_git_commit_metadata
from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition


def get_local_branch_name(project_dir: str) -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_dir)
        .decode("utf-8")
        .strip()
    )


def get_local_repo_name(project_dir: str) -> str:
    repo_url = (
        subprocess.check_output(["git", "config", "--get", "remote.origin.url"], cwd=project_dir)
        .decode("utf-8")
        .strip()
    )

    # Handle both SSH URLs (git@github.com:org/repo.git) and https URLs (https://github.com/org/repo.git)
    delimiters = r"[:/]"

    split_repo_url = re.split(delimiters, repo_url)
    # Extract just the org/repo part from the git URL
    return split_repo_url[-2] + "/" + split_repo_url[-1].replace(".git", "")


def _get_local_commit_hash(project_dir: str) -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_dir)
        .decode("utf-8")
        .strip()
    )


def create_or_update_branch_deployment_from_local_git_context(
    dagster_cloud_org_url: str,
    dagster_cloud_api_token: str,
    project_dir: str,
    mark_closed: bool,
    base_deployment_name: Optional[str],
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition],
) -> Optional[str]:
    branch_name = get_local_branch_name(project_dir)

    if not branch_name:
        raise Exception("Could not determine branch name from local git context")

    # Extract just the org/repo part from the git URL
    repo_name = get_local_repo_name(project_dir)

    if not repo_name:
        raise Exception("Could not determine repo name from local git context")

    commit_hash = _get_local_commit_hash(project_dir)

    git_metadata = get_git_commit_metadata(project_dir)

    try:
        timestamp = float(git_metadata["timestamp"])
    except Exception:
        logging.warn("Could not determine commit timestamp from git metadata, using current time")
        timestamp = time.time()

    commit_msg = git_metadata["message"]
    author_name = git_metadata["name"]
    author_email = git_metadata["email"]

    with gql.graphql_client_from_url(dagster_cloud_org_url, dagster_cloud_api_token) as client:
        deployment_name = gql.create_or_update_branch_deployment(
            client,
            repo_name=repo_name,
            branch_name=branch_name,
            commit_hash=commit_hash,
            timestamp=timestamp,
            author_name=author_name,
            author_email=author_email,
            commit_message=commit_msg,
            pull_request_status="CLOSED" if mark_closed else "OPEN",
            base_deployment_name=base_deployment_name,
            snapshot_base_condition=snapshot_base_condition,
        )
    return deployment_name


def create_or_update_branch_deployment_from_github_context(
    dagster_cloud_org_url: str,
    dagster_cloud_api_token: str,
    github_event: github_context.GithubEvent,
    mark_closed: bool,
    base_deployment_name: Optional[str],
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition],
) -> Optional[str]:
    """Return the branch deployment associated with the github PR."""
    event = github_event
    logging.debug("Read github event GithubEvent(%r)", event.__dict__)
    if not event.branch_name:
        return None
    else:
        url = f"{dagster_cloud_org_url}"
        with gql.graphql_client_from_url(url, dagster_cloud_api_token) as client:
            deployment_name = gql.create_or_update_branch_deployment(
                client,
                repo_name=event.repo_name,
                branch_name=event.branch_name,
                commit_hash=event.github_sha,
                timestamp=event.timestamp,
                branch_url=event.branch_url,
                pull_request_url=event.pull_request_url,
                pull_request_status="CLOSED" if mark_closed else event.pull_request_status,
                pull_request_number=event.pull_request_id,
                author_name=event.author_name,
                author_email=event.author_email,
                commit_message=event.commit_msg,
                author_avatar_url=github_event.get_github_avatar_url(),
                base_deployment_name=base_deployment_name,
                snapshot_base_condition=snapshot_base_condition,
            )
        return deployment_name
