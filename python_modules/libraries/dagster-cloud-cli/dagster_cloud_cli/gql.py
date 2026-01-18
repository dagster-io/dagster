from collections.abc import Generator, Sequence
from contextlib import contextmanager, suppress
from enum import Enum
from typing import Any, Optional, cast

from dagster_cloud_cli.core.graphql_client import (
    DagsterCloudGraphQLClient,
    create_cloud_webserver_client,
)
from dagster_cloud_cli.types import CliEventType, SnapshotBaseDeploymentCondition


@contextmanager
def graphql_client_from_url(
    url: str,
    token: str,
    retries: int = 3,
    deployment_name: Optional[str] = None,
    headers: Optional[dict[str, Any]] = None,
) -> Generator[DagsterCloudGraphQLClient, None, None]:
    with create_cloud_webserver_client(
        url.rstrip("/"), token, retries, deployment_name=deployment_name, headers=headers
    ) as client:
        yield client


def url_from_config(organization: str, deployment: Optional[str] = None) -> str:
    """Gets the Cloud webserver base url for a given organization and API token.
    Uses the default deployment if none is specified.
    """
    # Return the root URL / root GQL endpoint if no deployment is provided
    if not deployment:
        return f"https://{organization}.dagster.cloud"

    return f"https://{organization}.dagster.cloud/{deployment}"


FULL_DEPLOYMENTS_QUERY = """
query CliDeploymentsQuery {
    fullDeployments {
        deploymentName
        deploymentId
        deploymentType
    }
}
"""


def fetch_full_deployments(client: DagsterCloudGraphQLClient) -> list[Any]:
    return client.execute(FULL_DEPLOYMENTS_QUERY)["data"]["fullDeployments"]


class CliInputCodeLocation:
    def __init__(
        self,
        name: str,
        python_file: Optional[str] = None,
        package_name: Optional[str] = None,
        image: Optional[str] = None,
        module_name: Optional[str] = None,
        working_directory: Optional[str] = None,
        executable_path: Optional[str] = None,
        attribute: Optional[str] = None,
        commit_hash: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.name = name

        if len([val for val in [python_file, package_name, module_name] if val]) != 1:
            raise Exception(
                "Must specify exactly one of --python-file or --package-name or --module-name."
            )

        self.python_file = python_file
        self.package_name = package_name
        self.image = image
        self.module_name = module_name
        self.working_directory = working_directory
        self.executable_path = executable_path
        self.attribute = attribute
        self.commit_hash = commit_hash
        self.url = url

    def get_location_input(self):
        location_input = {"name": self.name}

        if self.python_file:
            location_input["pythonFile"] = self.python_file
        if self.package_name:
            location_input["packageName"] = self.package_name
        if self.image:
            location_input["image"] = self.image
        if self.module_name:
            location_input["moduleName"] = self.module_name
        if self.working_directory:
            location_input["workingDirectory"] = self.working_directory
        if self.executable_path:
            location_input["executablePath"] = self.executable_path
        if self.attribute:
            location_input["attribute"] = self.attribute
        if self.commit_hash:
            location_input["commitHash"] = self.commit_hash
        if self.url:
            location_input["url"] = self.url

        return location_input


AGENT_STATUS_QUERY = """
query CliAgentStatus {
    agents {
        status
        errors {
            error {
                message
            }
        }
    }
}
"""


class DagsterPlusDeploymentAgentType(Enum):
    SERVERLESS = "SERVERLESS"
    HYBRID = "HYBRID"


def fetch_agent_status(client: DagsterCloudGraphQLClient) -> list[Any]:
    return client.execute(AGENT_STATUS_QUERY)["data"]["agents"]


AGENT_TYPE_QUERY = """
query DeploymentInfoQuery {
	currentDeployment {
        agentType
    }
}
"""


def fetch_agent_type(client: DagsterCloudGraphQLClient) -> DagsterPlusDeploymentAgentType:
    return DagsterPlusDeploymentAgentType(
        client.execute(AGENT_TYPE_QUERY)["data"]["currentDeployment"]["agentType"]
    )


WORKSPACE_ENTRIES_QUERY = """
query CliWorkspaceEntries {
    workspace {
        workspaceEntries {
            locationName
            serializedDeploymentMetadata
        }
    }
}
"""


def fetch_workspace_entries(client: DagsterCloudGraphQLClient) -> list[Any]:
    return client.execute(WORKSPACE_ENTRIES_QUERY)["data"]["workspace"]["workspaceEntries"]


REPOSITORY_LOCATIONS_QUERY = """
query CliLocationsQuery {
  workspaceOrError {
    __typename
    ... on Workspace {
        locationEntries {
            __typename
            name
            loadStatus
            locationOrLoadError {
                __typename
                ... on RepositoryLocation {
                    name
                }
                ... on PythonError {
                    message
                    stack
                    errorChain {
                        isExplicitLink
                        error {
                            message
                            stack
                        }
                    }
                }
            }
        }
    }
    ... on PythonError {
        message
        stack
    }
  }
}
"""


def fetch_code_locations(client: DagsterCloudGraphQLClient) -> list[Any]:
    result = client.execute(REPOSITORY_LOCATIONS_QUERY)["data"]["workspaceOrError"]
    if result["__typename"] != "Workspace":
        raise Exception("Unable to query code locations: ", result["message"])
    return result["locationEntries"]


ADD_OR_UPDATE_LOCATION_FROM_DOCUMENT_MUTATION = """
mutation CliAddOrUpdateLocation($document: GenericScalar!) {
    addOrUpdateLocationFromDocument(document: $document) {
        __typename
        ... on WorkspaceEntry {
            locationName
        }
        ... on PythonError {
            message
            stack
        }
        ... on InvalidLocationError {
            errors
        }
        ... on UnauthorizedError {
            message
        }
    }
}
"""


def add_or_update_code_location(
    client: DagsterCloudGraphQLClient, location_document: dict[str, Any]
) -> None:
    result = client.execute(
        ADD_OR_UPDATE_LOCATION_FROM_DOCUMENT_MUTATION,
        variable_values={"document": location_document},
    )["data"]["addOrUpdateLocationFromDocument"]
    if result["__typename"] == "InvalidLocationError":
        raise Exception("Error in location config:\n" + "\n".join(result["errors"]))
    elif result["__typename"] != "WorkspaceEntry":
        raise Exception("Unable to add/update code location: ", result["message"])


DELETE_LOCATION_MUTATION = """
mutation CliDeleteLocation($locationName: String!) {
    deleteLocation(locationName: $locationName) {
        __typename
        ... on DeleteLocationSuccess {
            locationName
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def delete_code_location(client: DagsterCloudGraphQLClient, location_name: str) -> None:
    result = client.execute(
        DELETE_LOCATION_MUTATION, variable_values={"locationName": location_name}
    )

    if result["data"]["deleteLocation"]["__typename"] != "DeleteLocationSuccess":
        raise Exception(f"Unable to delete location: {result['data']['deleteLocation']}")


RECONCILE_LOCATIONS_FROM_DOCUMENT_MUTATION = """
mutation CliReconcileLocationsFromDoc($document: GenericScalar!) {
    reconcileLocationsFromDocument(document: $document) {
        __typename
        ... on ReconcileLocationsSuccess {
            locations {
                locationName
            }
        }
        ... on PythonError {
            message
            stack
        }
        ... on InvalidLocationError {
            errors
        }
    }
}
"""


def reconcile_code_locations(
    client: DagsterCloudGraphQLClient, locations_document: dict[str, Any]
) -> list[str]:
    result = client.execute(
        RECONCILE_LOCATIONS_FROM_DOCUMENT_MUTATION,
        variable_values={"document": locations_document},
    )

    if (
        result["data"]["reconcileLocationsFromDocument"]["__typename"]
        == "ReconcileLocationsSuccess"
    ):
        return sorted(
            [
                location["locationName"]
                for location in result["data"]["reconcileLocationsFromDocument"]["locations"]
            ]
        )
    elif result["data"]["reconcileLocationsFromDocument"] == "InvalidLocationError":
        raise Exception("Error in workspace config:\n" + "\n".join(result["errors"]))
    else:
        raise Exception(f"Unable to sync locations: {result}")


DEPLOY_LOCATIONS_FROM_DOCUMENT_MUTATION = """
mutation CliDeployLocations($document: GenericScalar!) {
    deployLocations(document: $document) {
        __typename
        ... on DeployLocationsSuccess {
            locations {
                locationName
            }
        }
        ... on PythonError {
            message
            stack
        }
        ... on InvalidLocationError {
            errors
        }
    }
}
"""


def deploy_code_locations(
    client: DagsterCloudGraphQLClient,
    locations_document: dict[str, Any],
) -> list[str]:
    result = client.execute(
        DEPLOY_LOCATIONS_FROM_DOCUMENT_MUTATION,
        variable_values={
            "document": locations_document,
        },
    )

    if result["data"]["deployLocations"]["__typename"] == "DeployLocationsSuccess":
        return sorted(
            [
                location["locationName"]
                for location in result["data"]["deployLocations"]["locations"]
            ]
        )
    elif result["data"]["deployLocations"] == "InvalidLocationError":
        raise Exception("Error in workspace config:\n" + "\n".join(result["errors"]))
    else:
        raise Exception(f"Unable to deploy locations: {result}")


GET_LOCATIONS_AS_DOCUMENT_QUERY = """
query CliLocationsAsDocument {
    locationsAsDocument {
        __typename
        document
    }
}
"""


def fetch_locations_as_document(client: DagsterCloudGraphQLClient) -> dict[str, Any]:
    result = client.execute(GET_LOCATIONS_AS_DOCUMENT_QUERY)

    return result["data"]["locationsAsDocument"]["document"]


SET_DEPLOYMENT_SETTINGS_MUTATION = """
    mutation CliSetDeploymentSettings($deploymentSettings: DeploymentSettingsInput!) {
        setDeploymentSettings(deploymentSettings: $deploymentSettings) {
            __typename
            ... on DeploymentSettings {
                settings
            }
            ...on UnauthorizedError {
                message
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""


def set_deployment_settings(
    client: DagsterCloudGraphQLClient, deployment_settings: dict[str, Any]
) -> None:
    result = client.execute(
        SET_DEPLOYMENT_SETTINGS_MUTATION,
        variable_values={"deploymentSettings": deployment_settings},
    )

    if result["data"]["setDeploymentSettings"]["__typename"] != "DeploymentSettings":
        raise Exception(f"Unable to set deployment settings: {result}")


DEPLOYMENT_SETTINGS_QUERY = """
    query CliDeploymentSettings {
        deploymentSettings {
            settings
        }
    }
"""


def get_deployment_settings(client: DagsterCloudGraphQLClient) -> dict[str, Any]:
    result = client.execute(DEPLOYMENT_SETTINGS_QUERY)

    if result.get("data", {}).get("deploymentSettings", {}).get("settings") is None:
        raise Exception(f"Unable to get deployment settings: {result}")

    return result["data"]["deploymentSettings"]["settings"]


ALERT_POLICIES_QUERY = """
    query CliAlertPoliciesDocument {
        alertPoliciesAsDocumentOrError {
            __typename
            ... on AlertPoliciesAsDocument {
                document
            }
            ... on PythonError {
                message
                stack
            }
            ... on UnauthorizedError {
                message
            }
        }
    }
"""


def get_alert_policies(client: DagsterCloudGraphQLClient) -> dict[str, Any]:
    result = client.execute(ALERT_POLICIES_QUERY)

    if (
        not result.get("data", {}).get("alertPoliciesAsDocumentOrError", {})
        or result.get("data", {}).get("alertPoliciesAsDocumentOrError", {}).get("__typename")
        != "AlertPoliciesAsDocument"
    ):
        raise Exception(f"Unable to get alert policies: {result}")

    return result["data"]["alertPoliciesAsDocumentOrError"]["document"]


RECONCILE_ALERT_POLICIES_FROM_DOCUMENT_MUTATION = """
    mutation CliReconcileAlertPoliciesFromDocumentMutation($document: GenericScalar!) {
        reconcileAlertPoliciesFromDocument(document: $document) {
            __typename
            ... on ReconcileAlertPoliciesSuccess {
                alertPolicies {
                    name
                }
            }
            ... on UnauthorizedError {
                message
            }
            ... on InvalidAlertPolicyError {
                message
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""


def reconcile_alert_policies(
    client: DagsterCloudGraphQLClient, alert_policy_inputs: Sequence[dict]
) -> Sequence[str]:
    result = client.execute(
        RECONCILE_ALERT_POLICIES_FROM_DOCUMENT_MUTATION,
        variable_values={"document": alert_policy_inputs},
    )

    if (
        result["data"]["reconcileAlertPoliciesFromDocument"]["__typename"]
        != "ReconcileAlertPoliciesSuccess"
    ):
        raise Exception(f"Unable to reconcile alert policies: {result}")

    return sorted(
        alert_policy["name"]
        for alert_policy in result["data"]["reconcileAlertPoliciesFromDocument"]["alertPolicies"]
    )


SET_ORGANIZATION_SETTINGS_MUTATION = """
    mutation CliSetOrganizationSettings($organizationSettings: OrganizationSettingsInput!) {
        setOrganizationSettings(organizationSettings: $organizationSettings) {
            __typename
            ... on OrganizationSettings {
                settings
            }
            ...on UnauthorizedError {
                message
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""


def set_organization_settings(
    client: DagsterCloudGraphQLClient, organization_settings: dict[str, Any]
) -> None:
    result = client.execute(
        SET_ORGANIZATION_SETTINGS_MUTATION,
        variable_values={"organizationSettings": organization_settings},
    )

    if result["data"]["setOrganizationSettings"]["__typename"] != "OrganizationSettings":
        raise Exception(f"Unable to set organization settings: {result}")


ORGANIZATION_SETTINGS_QUERY = """
    query CliOrganizationSettings {
        organizationSettings {
            settings
        }
    }
"""


def get_organization_settings(client: DagsterCloudGraphQLClient) -> dict[str, Any]:
    result = client.execute(ORGANIZATION_SETTINGS_QUERY)

    if result.get("data", {}).get("organizationSettings", {}).get("settings") is None:
        raise Exception(f"Unable to get organization settings: {result}")

    return result["data"]["organizationSettings"]["settings"]


CREATE_OR_UPDATE_BRANCH_DEPLOYMENT = """
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


def create_or_update_branch_deployment(
    client: DagsterCloudGraphQLClient,
    repo_name: str,
    branch_name: str,
    commit_hash: str,
    timestamp: float,
    branch_url: Optional[str] = None,
    pull_request_url: Optional[str] = None,
    pull_request_status: Optional[str] = None,
    pull_request_number: Optional[str] = None,
    commit_message: Optional[str] = None,
    commit_url: Optional[str] = None,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    author_avatar_url: Optional[str] = None,
    base_deployment_name: Optional[str] = None,
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition] = None,
) -> str:
    result = client.execute(
        CREATE_OR_UPDATE_BRANCH_DEPLOYMENT,
        variable_values={
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
                "commitUrl": commit_url,
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

    name = result.get("data", {}).get("createOrUpdateBranchDeployment", {}).get("deploymentName")
    if name is None:
        raise Exception(f"Unable to create or update branch deployment: {result}")

    return cast("str", name)


GET_BRANCH_DEPLOYMENT_NAME = """
query CliGetBranchDeploymentName($repoName: String!, $branchName: String!) {
    getBranchDeploymentName(repoName: $repoName, branchName: $branchName)
}
"""


def get_branch_deployment_name(
    client: DagsterCloudGraphQLClient,
    repo_name: str,
    branch_name: str,
) -> str:
    result = client.execute(
        GET_BRANCH_DEPLOYMENT_NAME,
        variable_values={
            "repoName": repo_name,
            "branchName": branch_name,
        },
    )

    name = result.get("data", {}).get("getBranchDeploymentName")
    if name is None:
        raise Exception(f"Unable to get branch deployment name: {result}")

    return cast("str", name)


LAUNCH_RUN_MUTATION = """
    mutation CliLaunchRun($executionParams: ExecutionParams!) {
        launchRun(executionParams: $executionParams) {
            __typename
            ... on LaunchRunSuccess {
                run {
                    runId
                    tags {
                        key
                        value
                    }
                    status
                    runConfigYaml
                }
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""


def launch_run(
    client: DagsterCloudGraphQLClient,
    location_name: str,
    repo_name: str,
    job_name: str,
    tags: dict[str, Any],
    config: dict[str, Any],
    asset_keys: Optional[list[str]],
) -> str:
    formatted_tags = [{"key": cast("str", k), "value": cast("str", v)} for k, v in tags.items()]

    params: dict[str, Any] = {
        "selector": {
            "repositoryLocationName": location_name,
            "repositoryName": repo_name,
            "jobName": job_name,
            **(
                {"assetSelection": [{"path": path.split("/")} for path in asset_keys]}
                if asset_keys
                else {}
            ),
        },
        "runConfigData": config,
        "executionMetadata": {"tags": formatted_tags},
    }
    result = client.execute(
        LAUNCH_RUN_MUTATION,
        variable_values={"executionParams": params},
    )

    if result["data"]["launchRun"]["__typename"] != "LaunchRunSuccess":
        raise Exception(f"Unable to launch run: {result}")

    return result["data"]["launchRun"]["run"]["runId"]


GET_ECR_CREDS_QUERY = """
query CliGetEcrInfo {
    serverless {
        awsRegion
        awsAuthToken
        registryAllowCustomBase
        registryUrl
    }
}
"""


def get_ecr_info(client: DagsterCloudGraphQLClient) -> Any:
    data = client.execute(GET_ECR_CREDS_QUERY)["data"]
    return {
        "registry_url": data["serverless"]["registryUrl"],
        "aws_region": data["serverless"]["awsRegion"],
        "aws_auth_token": data["serverless"]["awsAuthToken"],
        "allow_custom_base": data["serverless"]["registryAllowCustomBase"],
    }


GET_RUN_STATUS_QUERY = """
query CliGetRunStatus($runId: ID!) {
    runOrError(runId: $runId) {
        __typename
        ... on Run {
			id
			status
		}
    }
}
"""


def run_status(client: DagsterCloudGraphQLClient, run_id: str) -> Any:
    result = client.execute(
        GET_RUN_STATUS_QUERY,
        variable_values={"runId": run_id},
    )["data"]
    if result["runOrError"]["__typename"] != "Run" or result["runOrError"]["status"] is None:
        raise Exception(f"Unable to fetch run status: {result}")

    return result["runOrError"]["status"]


MARK_CLI_EVENT_MUTATION = """
 mutation MarkCliEventMutation(
   $eventType: CliEventType!
   $durationSeconds: Float!
   $success: Boolean
   $tags: [String]
   $message: String

 ) {
   markCliEvent(eventType: $eventType, durationSeconds: $durationSeconds, success: $success, tags: $tags, message: $message)
 }
 """


def mark_cli_event(
    client: DagsterCloudGraphQLClient,
    event_type: CliEventType,
    duration_seconds: float,
    success: bool = True,
    tags: Optional[list[str]] = None,
    message: Optional[str] = None,
) -> Any:
    with suppress(Exception):
        result = client.execute(
            MARK_CLI_EVENT_MUTATION,
            variable_values={
                "eventType": event_type.name,
                "durationSeconds": duration_seconds,
                "success": success,
                "tags": tags,
                "message": message,
            },
        )
        return result["data"]["markCliEvent"] == "ok"


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


def get_deployment_by_name(client: DagsterCloudGraphQLClient, deployment: str) -> dict[str, Any]:
    result = client.execute(
        GET_DEPLOYMENT_BY_NAME_QUERY, variable_values={"deploymentName": deployment}
    )["data"]["deploymentByName"]
    if not result["__typename"] == "DagsterCloudDeployment":
        raise Exception(f"Unable to find deployment {deployment}")

    return result
    raise Exception(f"Unable to find deployment {deployment}")


def delete_branch_deployment(client: DagsterCloudGraphQLClient, deployment: str) -> Any:
    deployment_info = get_deployment_by_name(client, deployment)
    if not deployment_info["deploymentType"] == "BRANCH":
        raise Exception(f"Deployment {deployment} is not a branch deployment")

    result = client.execute(
        DELETE_DEPLOYMENT_MUTATION,
        variable_values={"deploymentId": deployment_info["deploymentId"]},
    )

    if result["data"]["deleteDeployment"]["__typename"] != "DagsterCloudDeployment":
        raise Exception(f"Unable to delete deployment: {result}")

    return result["data"]["deleteDeployment"]["deploymentId"]


SET_ATLAN_INTEGRATION_SETTINGS_MUTATION = """
    mutation CliSetAtlanIntegrationSettings($atlanIntegrationSettings: AtlanIntegrationSettingsInput!) {
        setAtlanIntegrationSettings(atlanIntegrationSettings: $atlanIntegrationSettings) {
            __typename
            ... on SetAtlanIntegrationSettingsSuccess {
                organization
                success
            }
            ...on UnauthorizedError {
                message
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""


DELETE_ATLAN_INTEGRATION_SETTINGS_MUTATION = """
    mutation CliDeleteAtlanIntegrationSettings {
        deleteAtlanIntegrationSettings {
            __typename
            ...on DeleteAtlanIntegrationSuccess {
                organization
                success
            }
            ...on UnauthorizedError {
                message
            }
            ... on PythonError {
                message
                stack
            }
        }
    }
"""


GET_ATLAN_INTEGRATION_SETTINGS_QUERY = """
    query CliGetAtlanIntegrationSettings {
        atlanIntegration {
            atlanIntegrationSettingsOrError {
                __typename
                ... on AtlanIntegrationSettings {
                    token
                    domain
                }
                ... on AtlanIntegrationSettingsUnset {
                    __typename
                }
                ... on UnauthorizedError {
                    message
                }
                ... on PythonError {
                    message
                    stack
                }
            }
        }
    }
"""


ATLAN_INTEGRATION_PREFLIGHT_CHECK_QUERY = """
    query CliAtlanIntegrationPreflightCheck {
        atlanIntegration {
            atlanIntegrationPreflightCheckOrError {
                __typename
                ... on AtlanIntegrationPreflightCheckSuccess {
                    __typename
                    success
                }
                ... on AtlanIntegrationPreflightCheckFailure {
                    errorCode
                    errorMessage
                }
                ... on AtlanIntegrationSettingsUnset {
                    __typename
                }
                ... on UnauthorizedError {
                    message
                }
                ... on PythonError {
                    message
                    stack
                }
            }
        }
    }
"""


def set_atlan_integration_settings(
    client: DagsterCloudGraphQLClient,
    token: str,
    domain: str,
) -> tuple[str, bool]:
    result = client.execute(
        SET_ATLAN_INTEGRATION_SETTINGS_MUTATION,
        variable_values={"atlanIntegrationSettings": {"token": token, "domain": domain}},
    )

    if (
        result["data"]["setAtlanIntegrationSettings"]["__typename"]
        != "SetAtlanIntegrationSettingsSuccess"
    ):
        raise Exception(f"Unable to set Atlan integration settings: {result}")

    return result["data"]["setAtlanIntegrationSettings"]["organization"], result["data"][
        "setAtlanIntegrationSettings"
    ]["success"]


def delete_atlan_integration_settings(
    client: DagsterCloudGraphQLClient,
) -> tuple[str, bool]:
    result = client.execute(
        DELETE_ATLAN_INTEGRATION_SETTINGS_MUTATION,
    )

    if (
        result["data"]["deleteAtlanIntegrationSettings"]["__typename"]
        != "DeleteAtlanIntegrationSuccess"
    ):
        raise Exception(f"Unable to delete Atlan integration settings: {result}")

    return result["data"]["deleteAtlanIntegrationSettings"]["organization"], result["data"][
        "deleteAtlanIntegrationSettings"
    ]["success"]


def get_atlan_integration_settings(
    client: DagsterCloudGraphQLClient,
) -> dict:
    result = client.execute(
        GET_ATLAN_INTEGRATION_SETTINGS_QUERY,
    )

    settings_data = result["data"]["atlanIntegration"]["atlanIntegrationSettingsOrError"]
    typename = settings_data["__typename"]

    if typename == "AtlanIntegrationSettingsUnset":
        raise Exception("No Atlan integration settings configured")
    elif typename in ("UnauthorizedError", "PythonError"):
        raise Exception(f"Unable to get Atlan integration settings: {result}")

    return {
        "token": settings_data["token"],
        "domain": settings_data["domain"],
    }


def atlan_integration_preflight_check(
    client: DagsterCloudGraphQLClient,
) -> dict:
    result = client.execute(
        ATLAN_INTEGRATION_PREFLIGHT_CHECK_QUERY,
    )

    check_data = result["data"]["atlanIntegration"]["atlanIntegrationPreflightCheckOrError"]
    typename = check_data["__typename"]

    if typename == "AtlanIntegrationPreflightCheckSuccess":
        return {"success": True}
    elif typename == "AtlanIntegrationPreflightCheckFailure":
        return {
            "success": False,
            "error_code": check_data["errorCode"],
            "error_message": check_data["errorMessage"],
        }
    elif typename == "AtlanIntegrationSettingsUnset":
        raise Exception("No Atlan integration settings configured")
    else:
        raise Exception(f"Unable to perform Atlan integration preflight check: {result}")
