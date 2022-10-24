from abc import ABC, abstractmethod
from typing import Mapping, Optional

import pendulum
from croniter import croniter

from .events import AssetKey


class UpstreamMaterializationTimeConstraint(ABC):
    """Specifies a constraint on the timestamp of upstream data that was used for the most recent
    asset materialization of a given asset.

    The upstream materialization timestamp is calculated by traversing the history of asset
    materializations of upstream assets which occured before the current materialization. This
    gives a lower bound on the most recent records that could possibly be incorporated into the
    current state of the asset to which this constraint is attached.
    """

    @abstractmethod
    def minutes_late(
        self, current_timestamp: float, upstream_materialization_timestamp: Optional[float]
    ) -> Optional[float]:
        raise NotImplementedError()


class MinimumFreshnessConstraint(UpstreamMaterializationTimeConstraint):
    """This constraint specifies that the upstream data that was used for the most recent asset
    materialization must be materialized no more than `minimum_freshness_minutes` ago, relative to
    the current time.
    """

    def __init__(self, minimum_freshness_minutes: float):
        self._minimum_freshness_duration = pendulum.duration(minutes=minimum_freshness_minutes)

    def minutes_late(
        self, current_timestamp: float, upstream_materialization_timestamp: Optional[float]
    ) -> Optional[float]:
        if upstream_materialization_timestamp is None:
            return None

        upstream_datetime = pendulum.from_timestamp(upstream_materialization_timestamp)
        current_datetime = pendulum.from_timestamp(current_timestamp)

        minimum_datetime = current_datetime - self._minimum_freshness_duration

        if upstream_datetime >= minimum_datetime:
            return 0
        else:
            return (minimum_datetime - upstream_datetime).minutes


class CronMinimumFreshnessConstraint(UpstreamMaterializationTimeConstraint):
    """This constraint specifies that the upstream data that was used for the most recent asset
    materialization must be materialized no more than `minimum_freshness_minutes` ago, relative to
    the most recent cron schedule tick.
    """

    def __init__(self, cron_schedule: str, minimum_freshness_minutes: float):
        self._cron_schedule = cron_schedule
        self._minimum_freshness_duration = pendulum.duration(minutes=minimum_freshness_minutes)

    def minutes_late(
        self, current_timestamp: float, upstream_materialization_timestamp: Optional[float]
    ) -> Optional[float]:
        if upstream_materialization_timestamp is None:
            return None

        upstream_datetime = pendulum.from_timestamp(upstream_materialization_timestamp)
        current_datetime = pendulum.from_timestamp(current_timestamp)

        # find the most recent schedule tick which is more than minimum_freshness_duration old,
        # i.e. the most recent schedule tick which could be failing this constraint
        schedule_ticks = croniter(
            self._cron_schedule, current_datetime, ret_type=pendulum.DateTime, is_prev=True
        )
        latest_required_tick = next(schedule_ticks)
        while latest_required_tick + self._minimum_freshness_duration > current_datetime:
            latest_required_tick = next(schedule_ticks)
            print("...")
            print("dur", latest_required_tick + self._minimum_freshness_duration)
            print("lrt", latest_required_tick)

        print("ups", upstream_datetime)
        print("cur", current_datetime)
        print("latest", latest_required_tick)
        if upstream_datetime >= latest_required_tick:
            return 0
        else:
            # find the difference between the actual data time and the latest time that you would
            # have expected to get this data by
            expected_by_time = latest_required_tick + self._minimum_freshness_duration
            print("expected_by_time", expected_by_time)
            return current_datetime.diff(expected_by_time).in_minutes()


class FreshnessPolicy(ABC):
    """A FreshnessPolicy is a policy that defines how up-to-date a given asset is expected to be.
    We calculate the current time of the data within an asset by traversing the history of asset
    materializations of upstream assets which occured before the most recent materialization.

    This gives a lower bound on the most recent records that could possibly be incorporated into the
    current state of the asset to which this policy is attached.
    """

    @abstractmethod
    def minutes_late(
        self,
        current_timestamp: float,
        upstream_materialization_timestamps: Mapping[AssetKey, Optional[float]],
    ) -> Optional[float]:
        raise NotImplementedError()

    @staticmethod
    def minimum_freshness(minimum_freshness_minutes: float) -> "MinimumFreshnessPolicy":
        """Static constructor for a freshness policy which specifies that the upstream data that
        was used for the most recent asset materialization must have been materialized no more than
        `minimum_freshness_minutes` ago, relative to the current time.
        """
        return MinimumFreshnessPolicy(minimum_freshness_minutes=minimum_freshness_minutes)

    @staticmethod
    def cron_minimum_freshness(
        minimum_freshness_minutes: float, cron_schedule: str
    ) -> "CronMinimumFreshnessPolicy":
        """Static constructor for a freshness policy which specifies that the upstream data that
        was used for the most recent asset materialization must have been materialized no more than
        `minimum_freshness_minutes` ago, relative to the most recent cron schedule tick.
        """
        return CronMinimumFreshnessPolicy(
            minimum_freshness_minutes=minimum_freshness_minutes,
            cron_schedule=cron_schedule,
        )


class UniformFreshnessPolicy(FreshnessPolicy):
    """A freshness policy which applies the same constraint to all root asset materializations."""

    def __init__(self, constraint: UpstreamMaterializationTimeConstraint):
        self._constraint = constraint

    def minutes_late(
        self,
        current_timestamp: float,
        upstream_materialization_timestamps: Mapping[AssetKey, Optional[float]],
    ) -> Optional[float]:

        constraints_minutes_late = [
            self._constraint.minutes_late(current_timestamp, upstream_timestamp)
            for upstream_timestamp in upstream_materialization_timestamps.values()
        ]
        if any(val is None for val in constraints_minutes_late):
            return None
        else:
            return max(constraints_minutes_late)


class MinimumFreshnessPolicy(UniformFreshnessPolicy):
    """A freshness policy which specifies that the upstream data that was used for the most recent
    asset materialization must have been materialized no more than `minimum_freshness_minutes` ago,
    relative to the current time.
    """

    def __init__(self, minimum_freshness_minutes: float):
        super().__init__(
            constraint=MinimumFreshnessConstraint(
                minimum_freshness_minutes=minimum_freshness_minutes
            )
        )


class CronMinimumFreshnessPolicy(UniformFreshnessPolicy):
    """A freshness policy which specifies that the upstream data that was used for the most recent
    asset materialization must have been materialized no more than `minimum_freshness_minutes` ago,
    relative to the most recent cron schedule tick.
    """

    def __init__(self, minimum_freshness_minutes: float, cron_schedule: str):
        super().__init__(
            constraint=CronMinimumFreshnessConstraint(
                minimum_freshness_minutes=minimum_freshness_minutes,
                cron_schedule=cron_schedule,
            )
        )
