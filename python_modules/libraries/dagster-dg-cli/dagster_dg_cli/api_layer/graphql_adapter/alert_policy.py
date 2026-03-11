"""GraphQL implementation for alert policy operations."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.alert_policy import (
        AlertPolicyDocument,
        AlertPolicySyncResult,
    )

LIST_ALERT_POLICIES_QUERY = """
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

RECONCILE_ALERT_POLICIES_MUTATION = """
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


def process_alert_policies_response(graphql_response: dict[str, Any]) -> "AlertPolicyDocument":
    """Process GraphQL response into AlertPolicyDocument."""
    from dagster_dg_cli.api_layer.schemas.alert_policy import AlertPolicyDocument

    # After execute() unwraps, we get {"alertPoliciesAsDocumentOrError": {"document": ...}}
    inner = graphql_response.get("alertPoliciesAsDocumentOrError", {})
    typename = inner.get("__typename")

    if typename == "AlertPoliciesAsDocument":
        document = inner.get("document", {})
        # The document is a dict with an "alert_policies" key (list of policy dicts)
        alert_policies = document.get("alert_policies", []) if isinstance(document, dict) else []
        return AlertPolicyDocument(alert_policies=alert_policies)
    elif typename in ["PythonError", "UnauthorizedError"]:
        error_message = inner.get("message", "Unknown error")
        raise ValueError(f"Error fetching alert policies: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def process_reconcile_response(graphql_response: dict[str, Any]) -> "AlertPolicySyncResult":
    """Process GraphQL mutation response into AlertPolicySyncResult."""
    from dagster_dg_cli.api_layer.schemas.alert_policy import AlertPolicySyncResult

    # After execute() unwraps, we get {"reconcileAlertPoliciesFromDocument": {...}}
    inner = graphql_response.get("reconcileAlertPoliciesFromDocument", {})
    typename = inner.get("__typename")

    if typename == "ReconcileAlertPoliciesSuccess":
        policies = inner.get("alertPolicies", [])
        synced_names = sorted(p["name"] for p in policies)
        return AlertPolicySyncResult(synced_policies=synced_names)
    elif typename in ["UnauthorizedError", "InvalidAlertPolicyError", "PythonError"]:
        error_message = inner.get("message", "Unknown error")
        raise ValueError(f"Error reconciling alert policies: {error_message}")
    else:
        raise ValueError(f"Unexpected response type: {typename}")


def list_alert_policies_via_graphql(client: IGraphQLClient) -> "AlertPolicyDocument":
    """Fetch alert policies using GraphQL."""
    result = client.execute(LIST_ALERT_POLICIES_QUERY)
    return process_alert_policies_response(result)


def reconcile_alert_policies_via_graphql(
    client: IGraphQLClient, document: list[dict[str, Any]]
) -> "AlertPolicySyncResult":
    """Reconcile alert policies from a document using GraphQL."""
    result = client.execute(
        RECONCILE_ALERT_POLICIES_MUTATION,
        {"document": document},
    )
    return process_reconcile_response(result)
