"""GraphQL implementation for asset check operations."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset_check import (
        DgApiAssetCheckExecutionList,
        DgApiAssetCheckList,
    )

ASSET_CHECKS_QUERY = """
query AssetChecksQuery($assetKey: AssetKeyInput!) {
    assetChecksOrError(assetKey: $assetKey) {
        __typename
        ... on AssetChecks {
            checks {
                name
                description
                blocking
                jobNames
                canExecuteIndividually
                assetKey {
                    path
                }
            }
        }
        ... on NeedsMigration {
            message
        }
        ... on NeedsUserCodeUpgrade {
            message
        }
        ... on NeedsAgentUpgrade {
            message
        }
    }
}
"""

ASSET_CHECK_EXECUTIONS_QUERY = """
query AssetCheckExecutionsQuery(
    $assetKey: AssetKeyInput!,
    $checkName: String!,
    $limit: Int!,
    $cursor: String
) {
    assetCheckExecutions(
        assetKey: $assetKey,
        checkName: $checkName,
        limit: $limit,
        cursor: $cursor
    ) {
        id
        runId
        status
        timestamp
        stepKey
        evaluation {
            severity
            timestamp
            targetMaterialization {
                runId
                timestamp
            }
            metadataEntries {
                label
            }
        }
    }
}
"""


def process_asset_checks_response(
    graphql_response: dict[str, Any], asset_key: str
) -> "DgApiAssetCheckList":
    """Process GraphQL response into DgApiAssetCheckList."""
    from dagster_dg_cli.api_layer.schemas.asset_check import DgApiAssetCheck, DgApiAssetCheckList

    checks_result = graphql_response.get("assetChecksOrError")
    if not checks_result:
        raise Exception("No asset checks data in GraphQL response")

    typename = checks_result.get("__typename")
    if typename != "AssetChecks":
        error_msg = checks_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    checks_data = checks_result.get("checks", [])

    checks = []
    for c in checks_data:
        check_asset_key = "/".join(c.get("assetKey", {}).get("path", []))
        checks.append(
            DgApiAssetCheck(
                name=c["name"],
                asset_key=check_asset_key or asset_key,
                description=c.get("description"),
                blocking=c.get("blocking", False),
                job_names=c.get("jobNames", []),
                can_execute_individually=c.get("canExecuteIndividually"),
            )
        )

    return DgApiAssetCheckList(items=checks)


def process_asset_check_executions_response(
    graphql_response: dict[str, Any], asset_key: str, check_name: str
) -> "DgApiAssetCheckExecutionList":
    """Process GraphQL response into DgApiAssetCheckExecutionList."""
    from dagster_dg_cli.api_layer.schemas.asset_check import (
        DgApiAssetCheckExecution,
        DgApiAssetCheckExecutionList,
        DgApiAssetCheckExecutionStatus,
    )

    executions_data = graphql_response.get("assetCheckExecutions", [])

    executions = []
    for e in executions_data:
        executions.append(
            DgApiAssetCheckExecution(
                id=e["id"],
                run_id=e["runId"],
                status=DgApiAssetCheckExecutionStatus(e["status"]),
                timestamp=float(e["timestamp"]),
                step_key=e.get("stepKey"),
                check_name=check_name,
                asset_key=asset_key,
            )
        )

    return DgApiAssetCheckExecutionList(items=executions)


def list_asset_checks_via_graphql(client: IGraphQLClient, asset_key: str) -> "DgApiAssetCheckList":
    """Fetch asset checks using GraphQL."""
    asset_key_parts = asset_key.split("/")
    variables = {"assetKey": {"path": asset_key_parts}}
    result = client.execute(ASSET_CHECKS_QUERY, variables)
    return process_asset_checks_response(result, asset_key)


def get_asset_check_executions_via_graphql(
    client: IGraphQLClient,
    *,
    asset_key: str,
    check_name: str,
    limit: int = 25,
    cursor: str | None = None,
) -> "DgApiAssetCheckExecutionList":
    """Fetch asset check executions using GraphQL."""
    asset_key_parts = asset_key.split("/")
    variables: dict[str, Any] = {
        "assetKey": {"path": asset_key_parts},
        "checkName": check_name,
        "limit": limit,
    }
    if cursor:
        variables["cursor"] = cursor

    result = client.execute(ASSET_CHECK_EXECUTIONS_QUERY, variables)
    return process_asset_check_executions_response(result, asset_key, check_name)
