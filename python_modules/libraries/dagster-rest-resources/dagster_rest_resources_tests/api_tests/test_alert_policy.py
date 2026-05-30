from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.list_alert_policies import (
    ListAlertPolicies,
    ListAlertPoliciesAlertPoliciesAsDocumentOrErrorAlertPoliciesAsDocument,
    ListAlertPoliciesAlertPoliciesAsDocumentOrErrorPythonError,
    ListAlertPoliciesAlertPoliciesAsDocumentOrErrorUnauthorizedError,
)
from dagster_rest_resources.__generated__.reconcile_alert_policies import (
    ReconcileAlertPolicies,
    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentInvalidAlertPolicyError,
    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentPythonError,
    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentReconcileAlertPoliciesSuccess,
    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentReconcileAlertPoliciesSuccessAlertPolicies,
    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentUnauthorizedError,
)
from dagster_rest_resources.api.alert_policy import DgApiAlertPolicyApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.alert_policy import (
    DgApiAlertPolicyDocument,
    DgApiAlertPolicySyncResult,
)
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


class TestListAlertPolicies:
    def test_returns_alert_policies(self):
        document = {"alert_policies": [{"test_k": "test_v", "test_k_list": ["test_v_list"]}]}
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAlertPoliciesAsDocumentOrErrorAlertPoliciesAsDocument(
                __typename="AlertPoliciesAsDocument",
                document=document,
            )
        )
        result = DgApiAlertPolicyApi(client).list_alert_policies()

        assert result == DgApiAlertPolicyDocument(items=document["alert_policies"])

    def test_returns_empty_when_document_has_no_alert_policies(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAlertPoliciesAsDocumentOrErrorAlertPoliciesAsDocument(
                __typename="AlertPoliciesAsDocument",
                document={},
            )
        )
        result = DgApiAlertPolicyApi(client).list_alert_policies()

        assert result == DgApiAlertPolicyDocument(items=[])

    def test_none_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPoliciesAsDocumentOrError=None
        )

        with pytest.raises(
            DagsterPlusGraphqlError, match="No alert policies data in GraphQL response"
        ):
            DgApiAlertPolicyApi(client).list_alert_policies()

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAlertPoliciesAsDocumentOrErrorUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )
        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching alert policies"):
            DgApiAlertPolicyApi(client).list_alert_policies()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAlertPoliciesAsDocumentOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching alert policies"):
            DgApiAlertPolicyApi(client).list_alert_policies()


class TestActionSyncAlertPolicies:
    def test_returns_sorted_synced_policy_names(self):
        client = Mock(spec=IGraphQLClient)
        client.reconcile_alert_policies.return_value = ReconcileAlertPolicies(
            reconcileAlertPoliciesFromDocument=ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentReconcileAlertPoliciesSuccess(
                __typename="ReconcileAlertPoliciesSuccess",
                alertPolicies=[
                    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentReconcileAlertPoliciesSuccessAlertPolicies(
                        name="policy-b"
                    ),
                    ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentReconcileAlertPoliciesSuccessAlertPolicies(
                        name="policy-a"
                    ),
                ],
            )
        )
        policies = [{"name": "my-policy"}]
        result = DgApiAlertPolicyApi(client).action_sync_alert_policies(policies)

        client.reconcile_alert_policies.assert_called_once_with(
            document={"alert_policies": policies}
        )
        assert result == DgApiAlertPolicySyncResult(items=["policy-a", "policy-b"])

    def test_invalid_alert_policy_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.reconcile_alert_policies.return_value = ReconcileAlertPolicies(
            reconcileAlertPoliciesFromDocument=ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentInvalidAlertPolicyError(
                __typename="InvalidAlertPolicyError", message=""
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Invalid alert policy"):
            DgApiAlertPolicyApi(client).action_sync_alert_policies([])

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.reconcile_alert_policies.return_value = ReconcileAlertPolicies(
            reconcileAlertPoliciesFromDocument=ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )
        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching alert policies"):
            DgApiAlertPolicyApi(client).action_sync_alert_policies([])

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.reconcile_alert_policies.return_value = ReconcileAlertPolicies(
            reconcileAlertPoliciesFromDocument=ReconcileAlertPoliciesReconcileAlertPoliciesFromDocumentPythonError(
                __typename="PythonError", message=""
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error reconciling alert policies"):
            DgApiAlertPolicyApi(client).action_sync_alert_policies([])
