from typing import Mapping, Optional

import pendulum
from croniter import croniter

from .events import AssetKey


class RootDataTimeConstraint:
    """Specifies a constraint on the timestamp of the root data that was used for the most recent
    asset materialization of a given asset.

    The root data timestamp is calculated by traversing the history of asset materializations of
    upstream assets which occured before the current materialization. This gives a lower bound on
    the most recent records that could possibly be incorporated into the current state of the asset
    to which this SLA is attached.
    """

    def is_passing(self, root_data_timestamp: Optional[float]) -> bool:
        pass


class StalenessConstraint(RootDataTimeConstraint):
    """This constraint specifies that the root data that was used for the most recent asset
    materialization must not be more than `allowed_staleness_minutes` old, relative to the current
    time.
    """

    def __init__(self, allowed_staleness_minutes: float):
        self._allowed_staleness = pendulum.duration(minutes=allowed_staleness_minutes)

    def is_passing(self, root_data_timestamp: Optional[float]) -> bool:
        if root_data_timestamp is None:
            return False

        return (
            pendulum.from_timestamp(root_data_timestamp) > pendulum.now() - self._allowed_staleness
        )


class CronStalenessConstraint(RootDataTimeConstraint):
    """This constraint specifies that the root data that was used for the most recent asset
    materialization must not be more than `allowed_staleness_minutes` old, relative to the most
    recent cron schedule tick.
    """

    def __init__(self, cron_schedule: str, allowed_staleness_minutes: float):
        self._cron_schedule = cron_schedule
        self._allowed_staleness = pendulum.duration(minutes=allowed_staleness_minutes)

    def is_passing(self, root_data_timestamp: Optional[float]) -> bool:
        if root_data_timestamp is None:
            return False

        now = pendulum.now()

        # find the most recent root data time that could possibly be missing its SLA
        schedule_ticks = croniter(
            self._cron_schedule, now, ret_type=pendulum.DateTime, is_prev=True
        )
        latest_tick = next(schedule_ticks)
        while latest_tick + self._allowed_staleness > now:
            latest_tick = next(schedule_ticks)

        return pendulum.from_timestamp(root_data_timestamp) > latest_tick


class AssetRootDataSLA:
    """Specifies a set of constraints on the timestamps of the root data assets that were used for
    the most recent asset materialization of a given asset.

    The root data timestamps are calculated by traversing the history of asset materializations of
    upstream assets which occured before the current materialization. This gives a lower bound on
    the most recent records that could possibly be incorporated into the current state of the asset
    to which this SLA is attached.
    """

    def is_passing(self, root_data_timestamps: Mapping[AssetKey, float]) -> bool:
        pass


class UniformConstraintSLA(AssetRootDataSLA):
    """This base class applies the same constraint to each root asset."""

    def __init__(self, constraint: RootDataTimeConstraint):
        self._constraint = constraint

    def is_passing(self, root_data_timestamps: Mapping[AssetKey, Optional[float]]) -> bool:
        return all(
            self._constraint.is_passing(timestamp) for timestamp in root_data_timestamps.values()
        )


class StalenessSLA(UniformConstraintSLA):
    """This constraint specifies that the root data that was used for the most recent asset
    materialization must not be more than `allowed_staleness_minutes` old, relative to the current
    time.
    """

    def __init__(self, allowed_staleness_minutes: float):
        super().__init__(constraint=StalenessConstraint(allowed_staleness_minutes))


class CronStalenessSLA(UniformConstraintSLA):
    """This constraint specifies that the root data that was used for the most recent asset
    materialization must not be more than `allowed_staleness_minutes` old, relative to the most
    recent cron schedule tick.
    """

    def __init__(self, cron_schedule: str, allowed_staleness_minutes: float):
        super().__init__(
            constraint=CronStalenessConstraint(cron_schedule, allowed_staleness_minutes)
        )
