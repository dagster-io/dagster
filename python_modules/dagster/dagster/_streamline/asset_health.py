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
