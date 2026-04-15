"""Alert policy endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.alert_policy import (
    list_alert_policies_via_graphql,
    reconcile_alert_policies_via_graphql,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.alert_policy import (
        AlertPolicyDocument,
        AlertPolicySyncResult,
    )


@dataclass(frozen=True)
class DgApiAlertPolicyApi:
    client: IGraphQLClient

    def list_alert_policies(self) -> "AlertPolicyDocument":
        return list_alert_policies_via_graphql(self.client)

    def sync_alert_policies(self, document: list[dict[str, Any]]) -> "AlertPolicySyncResult":
        return reconcile_alert_policies_via_graphql(self.client, document)
