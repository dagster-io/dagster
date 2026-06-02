from dataclasses import dataclass
from typing import Any

from typing_extensions import assert_never

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.alert_policy import (
    DgApiAlertPolicyDocument,
    DgApiAlertPolicySyncResult,
)
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


@dataclass(frozen=True)
class DgApiAlertPolicyApi:
    _client: IGraphQLClient

    def list_alert_policies(self) -> DgApiAlertPolicyDocument:
        result = self._client.list_alert_policies().alert_policies_as_document_or_error
        if result is None:
            raise DagsterPlusGraphqlError("No alert policies data in GraphQL response")

        match result.typename__:
            case "AlertPoliciesAsDocument":
                document = result.document  # ty: ignore[unresolved-attribute]
                alert_policies = (
                    document.get("alert_policies", []) if isinstance(document, dict) else []
                )
                return DgApiAlertPolicyDocument(items=alert_policies)
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(
                    f"Error fetching alert policies: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching alert policies: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def action_sync_alert_policies(
        self, document: list[dict[str, Any]]
    ) -> DgApiAlertPolicySyncResult:
        result = self._client.reconcile_alert_policies(
            document={"alert_policies": document}
        ).reconcile_alert_policies_from_document

        match result.typename__:
            case "ReconcileAlertPoliciesSuccess":
                return DgApiAlertPolicySyncResult(
                    items=sorted(p.name for p in result.alert_policies if p is not None)  # ty: ignore[unresolved-attribute]
                )
            case "InvalidAlertPolicyError":
                raise DagsterPlusGraphqlError(f"Invalid alert policy: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(
                    f"Error fetching alert policies: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error reconciling alert policies: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)
