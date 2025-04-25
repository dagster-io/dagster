from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._streamline.asset_health import AssetHealthStatus


@whitelist_for_serdes
@record.record
class AssetCheckHealthState:
    """Maintains a list of asset checks for the asset in each terminal state. If a check is in progress,
    it will not move to a new list until the execution is complete.
    """

    passing_checks: set[AssetCheckKey]
    failing_checks: set[AssetCheckKey]
    warning_checks: set[AssetCheckKey]
    all_checks: set[AssetCheckKey]

    @property
    def health_status(self) -> AssetHealthStatus:
        """Returns the health status of the asset based on the checks."""
        if len(self.all_checks) == 0:
            return AssetHealthStatus.NOT_APPLICABLE
        if len(self.failing_checks) > 0:
            return AssetHealthStatus.DEGRADED
        if len(self.warning_checks) > 0:
            return AssetHealthStatus.WARNING

        num_unexecuted = (
            len(self.all_checks)
            - len(self.passing_checks)
            - len(self.failing_checks)
            - len(self.warning_checks)
        )
        if num_unexecuted > 0:
            return AssetHealthStatus.UNKNOWN
        # all checks are passing
        return AssetHealthStatus.HEALTHY
