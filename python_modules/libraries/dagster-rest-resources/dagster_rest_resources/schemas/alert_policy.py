from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from dagster_rest_resources.__generated__.enums import AlertPolicyEventType, NotificationStatus
from dagster_rest_resources.schemas.util import DgApiList, DgApiPaginatedList


class DgApiAlertPolicyDocument(DgApiList[dict[str, Any]]):
    pass


class DgApiAlertPolicySyncResult(DgApiList[str]):
    pass


class DgApiAlertPolicyOptions(BaseModel):
    consecutive_failure_threshold: int | None = None
    include_description_in_notification: bool | None = None
    renotify_interval_minutes: int | None = None


class DgApiEmailNotification(BaseModel):
    kind: Literal["email"] = "email"
    email_addresses: list[str]


class DgApiEmailOwnersNotification(BaseModel):
    kind: Literal["email_owners"] = "email_owners"
    default_email_addresses: list[str]


class DgApiSlackNotification(BaseModel):
    kind: Literal["slack"] = "slack"
    slack_workspace_name: str
    slack_channel_name: str


class DgApiMicrosoftTeamsNotification(BaseModel):
    kind: Literal["microsoft_teams"] = "microsoft_teams"
    webhook_url: str


class DgApiPagerdutyNotification(BaseModel):
    kind: Literal["pagerduty"] = "pagerduty"
    integration_key: str


class DgApiWebhookNotification(BaseModel):
    kind: Literal["webhook"] = "webhook"
    webhook_url: str
    body_template: str


DgApiNotificationService = Annotated[
    DgApiEmailNotification
    | DgApiEmailOwnersNotification
    | DgApiSlackNotification
    | DgApiMicrosoftTeamsNotification
    | DgApiPagerdutyNotification
    | DgApiWebhookNotification,
    Field(discriminator="kind"),
]


class DgApiAlertPolicy(BaseModel):
    """A configured alert policy.

    `alert_targets` has 17 potential types returned from the gql api, so it is left as generic dict type
    to avoid having to duplicate the schema for every possible type.
    """

    id: str
    name: str
    description: str
    enabled: bool
    event_types: list[AlertPolicyEventType]
    tags: list[dict[str, Any]] | None = None
    notification_service: DgApiNotificationService
    alert_targets: list[dict[str, Any]]
    policy_options: DgApiAlertPolicyOptions


class DgApiAlertPolicyList(DgApiList[DgApiAlertPolicy]):
    pass


class DgApiAlertNotification(BaseModel):
    """One delivery attempt for an alert policy.

    There are many different kinds of notifications (run, asset, code location, etc.) with distinct fields.
    Any field that is not common across all notification types is stored in `details`.
    """

    id: str
    kind: str
    status: NotificationStatus
    send_timestamp: float
    error_message: str | None = None
    alert_policy_id: str | None = None
    details: dict[str, Any] = {}


class DgApiAlertNotificationList(DgApiPaginatedList[DgApiAlertNotification]):
    pass


class DgApiRunAlertNotifications(BaseModel):
    notifications: list[DgApiAlertNotification]
    alert_policies: list[DgApiAlertPolicy]


class DgApiAlertPolicyDeleteResult(BaseModel):
    name: str
