"""GraphQL mutations and queries for branch deployment operations."""

from typing import Any, Optional

import click
from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

# GraphQL mutation for creating or updating a branch deployment
CREATE_OR_UPDATE_BRANCH_DEPLOYMENT_MUTATION = """
mutation CliCreateOrUpdateBranchDeployment(
    $branchData: CreateOrUpdateBranchDeploymentInput!
    $commit: DeploymentCommitInput!
    $baseDeploymentName: String
    $snapshotBaseCondition: SnapshotBaseDeploymentCondition
) {
    createOrUpdateBranchDeployment(
        branchData: $branchData,
        commit: $commit,
        baseDeploymentName: $baseDeploymentName,
        snapshotBaseCondition: $snapshotBaseCondition,
    ) {
        __typename
        ... on DagsterCloudDeployment {
            deploymentId
            deploymentName
        }
        ... on PythonError {
            message
        }
    }
}
"""

# GraphQL query to get deployment by name
GET_DEPLOYMENT_BY_NAME_QUERY = """
query DeploymentByNameQuery($deploymentName: String!) {
    deploymentByName(name: $deploymentName) {
        __typename
        ... on DagsterCloudDeployment {
            deploymentName
            deploymentId
            deploymentType
        }
    }
}
"""

# GraphQL mutation to delete a deployment
DELETE_DEPLOYMENT_MUTATION = """
mutation CliDeleteDeployment($deploymentId: Int!) {
    deleteDeployment(deploymentId: $deploymentId) {
        __typename
        ... on DagsterCloudDeployment {
            deploymentId
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""

# GraphQL query to get branch deployment name from repo and branch
GET_BRANCH_DEPLOYMENT_NAME_QUERY = """
query CliGetBranchDeploymentName($repoName: String!, $branchName: String!) {
    getBranchDeploymentName(repoName: $repoName, branchName: $branchName)
}
"""


def create_or_update_branch_deployment(
    client: IGraphQLClient,
    repo_name: str,
    branch_name: str,
    commit_hash: str,
    timestamp: float,
    branch_url: Optional[str] = None,
    pull_request_url: Optional[str] = None,
    pull_request_status: Optional[str] = None,
    pull_request_number: Optional[str] = None,
    commit_message: Optional[str] = None,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    author_avatar_url: Optional[str] = None,
    base_deployment_name: Optional[str] = None,
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition] = None,
) -> str:
    """Create or update a branch deployment.

    Args:
        client: GraphQL client
        repo_name: Git repository name (e.g., "org/repo")
        branch_name: Git branch name
        commit_hash: Git commit hash
        timestamp: Commit timestamp (Unix time)
        branch_url: URL to the branch (optional)
        pull_request_url: URL to PR/MR (optional)
        pull_request_status: PR status (optional)
        pull_request_number: PR number/ID (optional)
        commit_message: Commit message (optional)
        author_name: Commit author name (optional)
        author_email: Commit author email (optional)
        author_avatar_url: Author avatar URL (optional)
        base_deployment_name: Base deployment for comparison (optional)
        snapshot_base_condition: When to snapshot base deployment (optional)

    Returns:
        Deployment name

    Raises:
        click.ClickException: If the mutation fails
    """
    result = client.execute(
        CREATE_OR_UPDATE_BRANCH_DEPLOYMENT_MUTATION,
        variables={
            "branchData": {
                "repoName": repo_name,
                "branchName": branch_name,
                "branchUrl": branch_url,
                "pullRequestUrl": pull_request_url,
                "pullRequestStatus": pull_request_status,
                "pullRequestNumber": pull_request_number,
            },
            "commit": {
                "commitHash": commit_hash,
                "timestamp": timestamp,
                "commitMessage": commit_message,
                "authorName": author_name,
                "authorEmail": author_email,
                "authorAvatarUrl": author_avatar_url,
            },
            "baseDeploymentName": base_deployment_name,
            "snapshotBaseCondition": snapshot_base_condition.name
            if snapshot_base_condition
            else None,
        },
    )

    deployment_data = result.get("createOrUpdateBranchDeployment")
    if not deployment_data:
        raise click.ClickException(f"Unable to create or update branch deployment: {result}")

    deployment_name = deployment_data.get("deploymentName")
    if not deployment_name:
        error_message = deployment_data.get("message", "Unknown error")
        raise click.ClickException(f"Failed to create or update branch deployment: {error_message}")

    return deployment_name


def get_deployment_by_name(client: IGraphQLClient, deployment_name: str) -> dict[str, Any]:
    """Get deployment information by name.

    Args:
        client: GraphQL client
        deployment_name: Name of the deployment

    Returns:
        Dictionary containing deployment information

    Raises:
        click.ClickException: If deployment not found or query fails
    """
    result = client.execute(
        GET_DEPLOYMENT_BY_NAME_QUERY, variables={"deploymentName": deployment_name}
    )

    deployment_data = result.get("deploymentByName")
    if not deployment_data:
        raise click.ClickException(f"Deployment '{deployment_name}' not found")

    if deployment_data.get("__typename") != "DagsterCloudDeployment":
        raise click.ClickException(f"Unable to find deployment '{deployment_name}'")

    return deployment_data


def delete_branch_deployment(client: IGraphQLClient, deployment_name: str) -> int:
    """Delete a branch deployment.

    Args:
        client: GraphQL client
        deployment_name: Name of the branch deployment to delete

    Returns:
        Deployment ID of the deleted deployment

    Raises:
        click.ClickException: If deployment is not a branch deployment or deletion fails
    """
    # First, get the deployment info to verify it's a branch deployment
    deployment_info = get_deployment_by_name(client, deployment_name)

    if deployment_info.get("deploymentType") != "BRANCH":
        raise click.ClickException(
            f"Deployment '{deployment_name}' is not a branch deployment "
            f"(type: {deployment_info.get('deploymentType')}). "
            "Only branch deployments can be deleted with this command."
        )

    deployment_id = deployment_info.get("deploymentId")
    if not deployment_id:
        raise click.ClickException(f"Unable to get deployment ID for '{deployment_name}'")

    # Now delete the deployment
    result = client.execute(DELETE_DEPLOYMENT_MUTATION, variables={"deploymentId": deployment_id})

    delete_data = result.get("deleteDeployment")
    if not delete_data:
        raise click.ClickException(f"Unable to delete deployment: {result}")

    if delete_data.get("__typename") != "DagsterCloudDeployment":
        error_message = delete_data.get("message", "Unknown error")
        raise click.ClickException(f"Failed to delete deployment: {error_message}")

    return deployment_id


def get_branch_deployment_name(client: IGraphQLClient, repo_name: str, branch_name: str) -> str:
    """Get the deployment name for a given repo and branch.

    Args:
        client: GraphQL client
        repo_name: Git repository name (e.g., "org/repo")
        branch_name: Git branch name

    Returns:
        Deployment name

    Raises:
        click.ClickException: If unable to get deployment name
    """
    result = client.execute(
        GET_BRANCH_DEPLOYMENT_NAME_QUERY,
        variables={"repoName": repo_name, "branchName": branch_name},
    )

    deployment_name = result.get("getBranchDeploymentName")
    if not deployment_name:
        raise click.ClickException(
            f"Unable to get branch deployment name for repo '{repo_name}' "
            f"and branch '{branch_name}': {result}"
        )

    return deployment_name
