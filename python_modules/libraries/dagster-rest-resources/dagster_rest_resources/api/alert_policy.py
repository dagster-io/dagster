from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.base_model import UNSET
from dagster_rest_resources.__generated__.fragments import AlertPolicyFields
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.alert_policy import (
    DgApiAlertNotification,
    DgApiAlertNotificationList,
    DgApiAlertPolicy,
    DgApiAlertPolicyDeleteResult,
    DgApiAlertPolicyDocument,
    DgApiAlertPolicyList,
    DgApiAlertPolicyOptions,
    DgApiAlertPolicySyncResult,
    DgApiEmailNotification,
    DgApiEmailOwnersNotification,
    DgApiMicrosoftTeamsNotification,
    DgApiNotificationService,
    DgApiPagerdutyNotification,
    DgApiRunAlertNotifications,
    DgApiSlackNotification,
    DgApiWebhookNotification,
)
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)

if TYPE_CHECKING:
    from dagster_rest_resources.__generated__.get_alert_policy import GetAlertPolicyAlertPolicyById


# common to every AlertNotification member; anything else is carried in `details`
_NOTIFICATION_COMMON = frozenset(
    {"typename__", "id", "status", "sendTimestamp", "errorMessage", "alertPolicyId"}
)


def _build_notification_service(service: Any) -> DgApiNotificationService:
    match service.typename__:
        case "EmailAlertPolicyNotification":
            return DgApiEmailNotification(email_addresses=list(service.email_addresses))
        case "EmailOwnersAlertPolicyNotification":
            return DgApiEmailOwnersNotification(
                default_email_addresses=list(service.default_email_addresses)
            )
        case "SlackAlertPolicyNotification":
            return DgApiSlackNotification(
                slack_workspace_name=service.slack_workspace_name,
                slack_channel_name=service.slack_channel_name,
            )
        case "MicrosoftTeamsAlertPolicyNotification":
            return DgApiMicrosoftTeamsNotification(webhook_url=service.webhook_url)
        case "PagerdutyAlertPolicyNotification":
            return DgApiPagerdutyNotification(integration_key=service.integration_key)
        case "WebhookAlertPolicyNotification":
            return DgApiWebhookNotification(
                webhook_url=service.webhook_url,
                body_template=service.body_template,
            )
        case unexpected:
            raise DagsterPlusGraphqlError(f"Unknown notification service: {unexpected}")


def _build_policy(policy: AlertPolicyFields) -> DgApiAlertPolicy:
    return DgApiAlertPolicy(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        enabled=policy.enabled,
        event_types=policy.event_types,
        tags=[t.model_dump(by_alias=True) for t in policy.tags] if policy.tags else None,
        notification_service=_build_notification_service(policy.notification_service),
        alert_targets=[t.model_dump(by_alias=True) for t in policy.alert_targets],
        policy_options=DgApiAlertPolicyOptions(
            consecutive_failure_threshold=policy.policy_options.consecutive_failure_threshold,
            include_description_in_notification=policy.policy_options.include_description_in_notification,
            renotify_interval_minutes=policy.policy_options.renotify_interval_minutes,
        ),
    )


def _build_notification(notification: Any) -> DgApiAlertNotification:
    raw = notification.model_dump(by_alias=True)
    return DgApiAlertNotification(
        id=raw["id"],
        kind=raw["__typename"],
        status=raw["status"],
        send_timestamp=raw["sendTimestamp"],
        error_message=raw.get("errorMessage"),
        alert_policy_id=raw.get("alertPolicyId"),
        details={
            k: v for k, v in raw.items() if k not in _NOTIFICATION_COMMON and k != "__typename"
        },
    )


@dataclass(frozen=True)
class DgApiAlertPolicyApi:
    _client: IGraphQLClient

    def list_alert_policies_as_document(self) -> DgApiAlertPolicyDocument:
        result = self._client.list_alert_policies_as_document().alert_policies_as_document_or_error
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

    def list_alert_policies(self) -> DgApiAlertPolicyList:
        policies = self._client.list_alert_policies().alert_policies
        return DgApiAlertPolicyList(items=[_build_policy(p) for p in policies])

    def get_alert_policy(self, alert_policy_id: str) -> DgApiAlertPolicy:
        policy: GetAlertPolicyAlertPolicyById | None = self._client.get_alert_policy(
            alert_policy_id=alert_policy_id
        ).alert_policy_by_id
        if policy is None:
            raise DagsterPlusGraphqlError(f"Alert policy not found: {alert_policy_id}")
        return _build_policy(policy)

    def list_alert_policies_for_job(
        self,
        job_name: str,
        repository_name: str,
        repository_location_name: str,
    ) -> DgApiAlertPolicyList:
        policies = self._client.get_alert_policies_for_job(
            job_name=job_name,
            repository_name=repository_name,
            repository_location_name=repository_location_name,
        ).alert_policies_for_job
        return DgApiAlertPolicyList(items=[_build_policy(p) for p in policies])

    def list_alert_policy_notifications(
        self,
        alert_policy_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> DgApiAlertNotificationList:
        result = self._client.get_alert_policy_notifications(
            alert_policy_id=alert_policy_id,
            limit=limit,
            cursor=cursor,
        ).alert_policy_notifications
        if result is None:
            return DgApiAlertNotificationList(items=[], cursor=None, has_more=False)
        return DgApiAlertNotificationList(
            items=[_build_notification(n) for n in result.results],
            cursor=result.cursor or None,
            has_more=result.has_more,
        )

    def get_run_alert_notifications(
        self,
        run_id: str,
        limit: int | None = None,
    ) -> DgApiRunAlertNotifications:
        result = self._client.get_run_alert_notifications(
            run_id=run_id,
            limit=limit if limit is not None else UNSET,
        ).run_notifications_or_error
        if result is None:
            raise DagsterPlusGraphqlError(f"No notifications data for run: {run_id}")

        match result.typename__:
            case "RunNotifications":
                return DgApiRunAlertNotifications(
                    notifications=[_build_notification(n) for n in result.notifications],  # ty: ignore[unresolved-attribute]
                    alert_policies=[_build_policy(p) for p in result.alert_policies],
                )
            case "RunNotificationsExpiredError":
                raise DagsterPlusGraphqlError(f"Run notifications have expired: {result.message}")
            case _ as unreachable:
                assert_never(unreachable)

    def create_alert_policy(self, document: dict[str, Any]) -> DgApiAlertPolicy:
        """Create or update a single alert policy from its config document.

        Unlike `action_sync_alert_policies`, this leaves policies absent from the document
        alone rather than deleting them.
        """
        result = self._client.create_or_update_alert_policy(
            document=document
        ).create_or_update_alert_policy_from_document

        match result.typename__:
            case "AlertPolicy":
                return _build_policy(result)
            case "CodeBackedAlertPolicyError":
                raise DagsterPlusGraphqlError(result.message)
            case "InvalidAlertPolicyError":
                raise DagsterPlusGraphqlError(f"Invalid alert policy: {result.message}")
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error saving alert policy: {result.message}")
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error saving alert policy: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def delete_alert_policy(self, alert_policy_name: str) -> DgApiAlertPolicyDeleteResult:
        result = self._client.delete_alert_policy(
            alert_policy_name=alert_policy_name
        ).delete_alert_policy

        match result.typename__:
            case "DeleteAlertPolicySuccess":
                return DgApiAlertPolicyDeleteResult(name=result.alert_policy_name)
            case "CodeBackedAlertPolicyError":
                raise DagsterPlusGraphqlError(result.message)
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error deleting alert policy: {result.message}")
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error deleting alert policy: {result.message}")  # ty: ignore[unresolved-attribute]
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
            case "CodeBackedAlertPolicyError":
                raise DagsterPlusGraphqlError(result.message)  # ty: ignore[unresolved-attribute]
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
