from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.delete_alert_policy import (
    DeleteAlertPolicy,
    DeleteAlertPolicyDeleteAlertPolicyDeleteAlertPolicySuccess,
    DeleteAlertPolicyDeleteAlertPolicyUnauthorizedError,
)
from dagster_rest_resources.__generated__.enums import AlertPolicyEventType, NotificationStatus
from dagster_rest_resources.__generated__.fragments import (
    AlertPolicyFieldsAlertTargetsAssetKeyTarget,
    AlertPolicyFieldsAlertTargetsAssetKeyTargetAssetKey,
    AlertPolicyFieldsNotificationServiceEmailAlertPolicyNotification,
    AlertPolicyFieldsNotificationServiceEmailOwnersAlertPolicyNotification,
    AlertPolicyFieldsNotificationServiceMicrosoftTeamsAlertPolicyNotification,
    AlertPolicyFieldsNotificationServicePagerdutyAlertPolicyNotification,
    AlertPolicyFieldsNotificationServiceSlackAlertPolicyNotification,
    AlertPolicyFieldsNotificationServiceWebhookAlertPolicyNotification,
    AlertPolicyFieldsPolicyOptions,
    AlertPolicyFieldsTags,
)
from dagster_rest_resources.__generated__.get_alert_policy import (
    GetAlertPolicy,
    GetAlertPolicyAlertPolicyById,
)
from dagster_rest_resources.__generated__.get_alert_policy_notifications import (
    GetAlertPolicyNotifications,
    GetAlertPolicyNotificationsAlertPolicyNotifications,
    GetAlertPolicyNotificationsAlertPolicyNotificationsResultsJobRunAlertNotification,
)
from dagster_rest_resources.__generated__.list_alert_policies import (
    ListAlertPolicies,
    ListAlertPoliciesAlertPolicies,
)
from dagster_rest_resources.__generated__.list_alert_policies_as_document import (
    ListAlertPoliciesAsDocument,
    ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorAlertPoliciesAsDocument,
    ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorPythonError,
    ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorUnauthorizedError,
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
    DgApiAlertPolicyOptions,
    DgApiAlertPolicySyncResult,
    DgApiEmailNotification,
    DgApiEmailOwnersNotification,
    DgApiMicrosoftTeamsNotification,
    DgApiPagerdutyNotification,
    DgApiSlackNotification,
    DgApiWebhookNotification,
)
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


class TestListAlertPolicies:
    def test_returns_alert_policies(self):
        document = {"alert_policies": [{"test_k": "test_v", "test_k_list": ["test_v_list"]}]}
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies_as_document.return_value = ListAlertPoliciesAsDocument(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorAlertPoliciesAsDocument(
                __typename="AlertPoliciesAsDocument",
                document=document,
            )
        )
        result = DgApiAlertPolicyApi(client).list_alert_policies_as_document()

        assert result == DgApiAlertPolicyDocument(items=document["alert_policies"])

    def test_returns_empty_when_document_has_no_alert_policies(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies_as_document.return_value = ListAlertPoliciesAsDocument(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorAlertPoliciesAsDocument(
                __typename="AlertPoliciesAsDocument",
                document={},
            )
        )
        result = DgApiAlertPolicyApi(client).list_alert_policies_as_document()

        assert result == DgApiAlertPolicyDocument(items=[])

    def test_none_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies_as_document.return_value = ListAlertPoliciesAsDocument(
            alertPoliciesAsDocumentOrError=None
        )

        with pytest.raises(
            DagsterPlusGraphqlError, match="No alert policies data in GraphQL response"
        ):
            DgApiAlertPolicyApi(client).list_alert_policies_as_document()

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies_as_document.return_value = ListAlertPoliciesAsDocument(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )
        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching alert policies"):
            DgApiAlertPolicyApi(client).list_alert_policies_as_document()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies_as_document.return_value = ListAlertPoliciesAsDocument(
            alertPoliciesAsDocumentOrError=ListAlertPoliciesAsDocumentAlertPoliciesAsDocumentOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )
        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching alert policies"):
            DgApiAlertPolicyApi(client).list_alert_policies_as_document()


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


def _make_policy_fields(**overrides) -> dict:
    fields = dict(
        id="policy-1",
        name="on-failure",
        description="notify on failure",
        tags=[AlertPolicyFieldsTags(key="team", value="data")],
        eventTypes=[AlertPolicyEventType.JOB_FAILURE],
        notificationService=AlertPolicyFieldsNotificationServiceSlackAlertPolicyNotification(
            __typename="SlackAlertPolicyNotification",
            slackWorkspaceName="dagster",
            slackChannelName="#alerts",
        ),
        enabled=True,
        alertTargets=[
            AlertPolicyFieldsAlertTargetsAssetKeyTarget(
                __typename="AssetKeyTarget",
                assetKey=AlertPolicyFieldsAlertTargetsAssetKeyTargetAssetKey(
                    path=["warehouse", "orders"]
                ),
            )
        ],
        policyOptions=AlertPolicyFieldsPolicyOptions(
            consecutiveFailureThreshold=2,
            includeDescriptionInNotification=True,
            renotifyIntervalMinutes=60,
        ),
    )
    fields.update(overrides)
    return fields


class TestListAlertPoliciesExpanded:
    def test_returns_policies(self):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPolicies=[ListAlertPoliciesAlertPolicies(**_make_policy_fields())]
        )

        result = DgApiAlertPolicyApi(_client=client).list_alert_policies()

        assert result.total == 1
        policy = result.items[0]
        assert policy.name == "on-failure"
        assert policy.enabled is True
        assert policy.event_types == [AlertPolicyEventType.JOB_FAILURE]
        assert policy.notification_service == DgApiSlackNotification(
            slack_workspace_name="dagster", slack_channel_name="#alerts"
        )
        assert policy.policy_options == DgApiAlertPolicyOptions(
            consecutive_failure_threshold=2,
            include_description_in_notification=True,
            renotify_interval_minutes=60,
        )
        # targets stay as the shapes graphql returned
        assert policy.alert_targets[0]["assetKey"] == {"path": ["warehouse", "orders"]}
        assert policy.tags == [{"key": "team", "value": "data"}]


class TestGetAlertPolicy:
    def test_returns_policy(self):
        client = Mock(spec=IGraphQLClient)
        client.get_alert_policy.return_value = GetAlertPolicy(
            alertPolicyById=GetAlertPolicyAlertPolicyById(**_make_policy_fields())
        )

        result = DgApiAlertPolicyApi(_client=client).get_alert_policy("policy-1")

        assert result.id == "policy-1"
        client.get_alert_policy.assert_called_once_with(alert_policy_id="policy-1")

    def test_missing_policy_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_alert_policy.return_value = GetAlertPolicy(alertPolicyById=None)

        with pytest.raises(DagsterPlusGraphqlError, match="Alert policy not found: nope"):
            DgApiAlertPolicyApi(_client=client).get_alert_policy("nope")


class TestListAlertPolicyNotifications:
    def test_splits_common_fields_from_kind_specific_details(self):
        client = Mock(spec=IGraphQLClient)
        client.get_alert_policy_notifications.return_value = GetAlertPolicyNotifications(
            alertPolicyNotifications=GetAlertPolicyNotificationsAlertPolicyNotifications(
                results=[
                    GetAlertPolicyNotificationsAlertPolicyNotificationsResultsJobRunAlertNotification(
                        __typename="JobRunAlertNotification",
                        id="n1",
                        status=NotificationStatus.SUCCESS,
                        sendTimestamp=1705311000.0,
                        errorMessage=None,
                        alertPolicyId="policy-1",
                        jobName="my_job",
                        codeLocationName="loc",
                        repositoryName="repo",
                        eventType=AlertPolicyEventType.JOB_FAILURE,
                        runId="run-1",
                    )
                ],
                cursor="next",
                hasMore=True,
            )
        )

        result = DgApiAlertPolicyApi(_client=client).list_alert_policy_notifications("policy-1")

        assert result.cursor == "next"
        assert result.has_more is True
        notification = result.items[0]
        assert notification.kind == "JobRunAlertNotification"
        assert notification.status == NotificationStatus.SUCCESS
        assert notification.alert_policy_id == "policy-1"
        # the run specific fields land in details rather than being dropped
        assert notification.details["jobName"] == "my_job"
        assert notification.details["runId"] == "run-1"
        assert "id" not in notification.details

    def test_missing_notifications_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.get_alert_policy_notifications.return_value = GetAlertPolicyNotifications(
            alertPolicyNotifications=None
        )

        result = DgApiAlertPolicyApi(_client=client).list_alert_policy_notifications("policy-1")

        assert result.items == []
        assert result.has_more is False


class TestDeleteAlertPolicy:
    def test_returns_deleted_name(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_alert_policy.return_value = DeleteAlertPolicy(
            deleteAlertPolicy=DeleteAlertPolicyDeleteAlertPolicyDeleteAlertPolicySuccess(
                __typename="DeleteAlertPolicySuccess", alertPolicyName="on-failure"
            )
        )

        result = DgApiAlertPolicyApi(_client=client).delete_alert_policy("on-failure")

        assert result.name == "on-failure"

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_alert_policy.return_value = DeleteAlertPolicy(
            deleteAlertPolicy=DeleteAlertPolicyDeleteAlertPolicyUnauthorizedError(
                __typename="UnauthorizedError", message="nope"
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error deleting alert policy"):
            DgApiAlertPolicyApi(_client=client).delete_alert_policy("on-failure")


class TestNotificationServiceKinds:
    @pytest.mark.parametrize(
        ("generated", "expected"),
        [
            (
                AlertPolicyFieldsNotificationServiceEmailAlertPolicyNotification(
                    __typename="EmailAlertPolicyNotification",
                    emailAddresses=["on-call@hooli.com"],
                ),
                DgApiEmailNotification(email_addresses=["on-call@hooli.com"]),
            ),
            (
                AlertPolicyFieldsNotificationServiceEmailOwnersAlertPolicyNotification(
                    __typename="EmailOwnersAlertPolicyNotification",
                    defaultEmailAddresses=["fallback@hooli.com"],
                ),
                DgApiEmailOwnersNotification(default_email_addresses=["fallback@hooli.com"]),
            ),
            (
                AlertPolicyFieldsNotificationServiceMicrosoftTeamsAlertPolicyNotification(
                    __typename="MicrosoftTeamsAlertPolicyNotification",
                    webhookUrl="https://teams.example/hook",
                ),
                DgApiMicrosoftTeamsNotification(webhook_url="https://teams.example/hook"),
            ),
            (
                AlertPolicyFieldsNotificationServicePagerdutyAlertPolicyNotification(
                    __typename="PagerdutyAlertPolicyNotification",
                    integrationKey="abc123",
                ),
                DgApiPagerdutyNotification(integration_key="abc123"),
            ),
            (
                AlertPolicyFieldsNotificationServiceWebhookAlertPolicyNotification(
                    __typename="WebhookAlertPolicyNotification",
                    webhookUrl="https://hooks.example/dagster",
                    bodyTemplate='{"text": "{{ message }}"}',
                ),
                DgApiWebhookNotification(
                    webhook_url="https://hooks.example/dagster",
                    body_template='{"text": "{{ message }}"}',
                ),
            ),
        ],
        ids=["email", "email_owners", "microsoft_teams", "pagerduty", "webhook"],
    )
    def test_each_kind_maps_to_its_own_model(self, generated, expected):
        client = Mock(spec=IGraphQLClient)
        client.list_alert_policies.return_value = ListAlertPolicies(
            alertPolicies=[
                ListAlertPoliciesAlertPolicies(**_make_policy_fields(notificationService=generated))
            ]
        )

        result = DgApiAlertPolicyApi(_client=client).list_alert_policies()

        assert result.items[0].notification_service == expected
