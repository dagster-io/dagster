import enum

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetHealthStatus(enum.Enum):
    """Enum for the health status of an asset."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@whitelist_for_serdes
@record.record
class AssetHealthState:
    asset_checks_status: AssetHealthStatus
    materialization_status: AssetHealthStatus
    freshness_status: AssetHealthStatus

    @property
    def asset_health(self):
        statuses = [
            self.materialization_status,
            self.asset_checks_status,
            self.freshness_status,
        ]
        if AssetHealthStatus.DEGRADED in statuses:
            return AssetHealthStatus.DEGRADED
        if AssetHealthStatus.WARNING in statuses:
            return AssetHealthStatus.WARNING
        # at this point, all statuses are HEALTHY, UNKNOWN, or NOT_APPLICABLE
        if self.materialization_status == AssetHealthStatus.UNKNOWN:
            return AssetHealthStatus.UNKNOWN
        if all(
            status == AssetHealthStatus.UNKNOWN or status == AssetHealthStatus.NOT_APPLICABLE
            for status in statuses
        ):
            return AssetHealthStatus.UNKNOWN
        # at least one status must be HEALTHY
        return AssetHealthStatus.HEALTHY

    @classmethod
    def default(cls) -> "AssetHealthState":
        return AssetHealthState(
            asset_checks_status=AssetHealthStatus.UNKNOWN,
            materialization_status=AssetHealthStatus.UNKNOWN,
            freshness_status=AssetHealthStatus.UNKNOWN,
        )
