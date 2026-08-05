from collections.abc import Mapping

from dagster._core.storage.tags import (
    AUTO_MATERIALIZE_TAG,
    AUTO_OBSERVE_TAG,
    BACKFILL_ID_TAG,
    HIDDEN_TAG_PREFIX,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
    ROOT_RUN_ID_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
    SYSTEM_TAG_PREFIX,
)

CLOUD_SYSTEM_TAG_PREFIX = "dagster-cloud/"

PEX_METADATA_TAG = f"{HIDDEN_TAG_PREFIX}pex_metadata"
PEX_TAG_TAG = f"{SYSTEM_TAG_PREFIX}pex_tag"
IGNORE_ALERTS_TAG = f"{CLOUD_SYSTEM_TAG_PREFIX}ignore-alerts"

RUN_TAG_RUN_COLUMN_TAG_KEYS = {
    AUTO_MATERIALIZE_TAG,
    AUTO_OBSERVE_TAG,
    REPOSITORY_LABEL_TAG,
    ROOT_RUN_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
    BACKFILL_ID_TAG,
}

DID_ALERT_TAG = f"{CLOUD_SYSTEM_TAG_PREFIX}triggered_alert"
TRIGGERED_ALERT_POLICY_TAG_PREFIX = f"{HIDDEN_TAG_PREFIX}triggered_alert_policy/"
TRIGGERED_ALERT_ID_TAG_PREFIX = f"{HIDDEN_TAG_PREFIX}triggered_alert/"

TRIGGERED_NOTIFICATION_TAG_PREFIX = f"{HIDDEN_TAG_PREFIX}triggered_notification/"


def get_triggered_alert_policy_key(alert_policy_id: str) -> str:
    return f"{TRIGGERED_ALERT_POLICY_TAG_PREFIX}{alert_policy_id}"


def get_triggered_alert_id_key(alert_id: str) -> str:
    return f"{TRIGGERED_ALERT_ID_TAG_PREFIX}{alert_id}"


def get_triggered_notification_key(notification_id: str) -> str:
    return f"{TRIGGERED_NOTIFICATION_TAG_PREFIX}{notification_id}"


def get_triggered_notification_key_value(notification_id: str) -> Mapping[str, str]:
    return {f"{TRIGGERED_NOTIFICATION_TAG_PREFIX}{notification_id}": "true"}


def get_policy_names_from_tag_value(policies_str):
    """From a comma-delineated string (whitespace allowed), retrieve alert policy names."""
    return [policy_name.strip() for policy_name in policies_str.split(",")]


def should_tag_be_used_for_indexing_filtering(tag_key: str) -> bool:
    """Determines whether a tag should be added to the run_tags table,
    which is used for indexing and filtering runs.
    Tags not added to the table will still be stored on the run object, but
    will not be directly queryable via the run_tags table.
    """
    if tag_key in RUN_TAG_RUN_COLUMN_TAG_KEYS:
        return False

    if tag_key.startswith(TRIGGERED_ALERT_ID_TAG_PREFIX) or tag_key.startswith(
        TRIGGERED_ALERT_POLICY_TAG_PREFIX
    ):
        return False

    return True
