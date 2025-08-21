import enum

from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetHealthStatus(enum.Enum):
    """Enum for the health status of an asset."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def overall_status_from_component_statuses(
    asset_checks_status: AssetHealthStatus,
    materialization_status: AssetHealthStatus,
    freshness_status: AssetHealthStatus,
) -> AssetHealthStatus:
    statuses = [
        materialization_status,
        asset_checks_status,
        freshness_status,
    ]
    if AssetHealthStatus.DEGRADED in statuses:
        return AssetHealthStatus.DEGRADED
    if AssetHealthStatus.WARNING in statuses:
        return AssetHealthStatus.WARNING

    # at this point, all statuses are HEALTHY, UNKNOWN, or NOT_APPLICABLE
    # if the materialization status is UNKNOWN, then we want overall status to be UNKNOWN,
    # even if other statuses are known
    if materialization_status == AssetHealthStatus.UNKNOWN:
        return AssetHealthStatus.UNKNOWN
    if all(
        status == AssetHealthStatus.UNKNOWN or status == AssetHealthStatus.NOT_APPLICABLE
        for status in statuses
    ):
        return AssetHealthStatus.UNKNOWN
    # at least one status must be HEALTHY
    return AssetHealthStatus.HEALTHY
