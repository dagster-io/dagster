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
    def is_passing(
        self, current_timestamp: float, upstream_materialization_timestamp: Optional[float]
    ) -> bool:
        raise NotImplementedError()


class MinimumFreshnessConstraint(UpstreamMaterializationTimeConstraint):
    """This constraint specifies that the upstream data that was used for the most recent asset
    materialization must be materialized no more than `minimum_freshness_minutes` ago, relative to
    the current time.
    """

    def __init__(self, minimum_freshness_minutes: float):
        self._minimum_freshness_minutes = minimum_freshness_minutes

    def is_passing(
        self, current_timestamp: float, upstream_materialization_timestamp: Optional[float]
    ) -> bool:
        if upstream_materialization_timestamp is None:
            return False

        upstream_datetime = pendulum.from_timestamp(upstream_materialization_timestamp)
        current_datetime = pendulum.from_timestamp(current_timestamp)

        minimum_datetime = current_datetime - pendulum.duration(
            minutes=self._minimum_freshness_minutes
        )

        return upstream_datetime >= minimum_datetime


class CronMinimumFreshnessConstraint(UpstreamMaterializationTimeConstraint):
    """This constraint specifies that the upstream data that was used for the most recent asset
    materialization must be materialized no more than `minimum_freshness_minutes` ago, relative to
    the most recent cron schedule tick.
    """

    def __init__(self, cron_schedule: str, minimum_freshness_minutes: float):
        self._cron_schedule = cron_schedule
        self._minimum_freshness_minutes = minimum_freshness_minutes

    def is_passing(
        self, current_timestamp: float, upstream_materialization_timestamp: Optional[float]
    ) -> bool:
        if upstream_materialization_timestamp is None:
            return False

        now = pendulum.from_timestamp(current_timestamp)

        # find the most recent schedule tick which could possibly be failing this constraint
        # (generally this is just the previous schedule tick)
        schedule_ticks = croniter(
            self._cron_schedule, now, ret_type=pendulum.DateTime, is_prev=True
        )
        latest_tick = next(schedule_ticks)
        while latest_tick + pendulum.duration(minutes=self._minimum_freshness_minutes) > now:
            latest_tick = next(schedule_ticks)

        return pendulum.from_timestamp(upstream_materialization_timestamp) > latest_tick


class FreshnessPolicy(ABC):
    """A FreshnessPolicy is a policy that defines how up-to-date a given asset is expected to be.
    We calculate the current time of the data within an asset by traversing the history of asset
    materializations of upstream assets which occured before the most recent materialization.

    This gives a lower bound on the most recent records that could possibly be incorporated into the
    current state of the asset to which this policy is attached.
    """

    @abstractmethod
    def is_passing(
        self,
        current_timestamp: float,
        upstream_materialization_timestamps: Mapping[AssetKey, Optional[float]],
    ) -> bool:
        raise NotImplementedError

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

    def is_passing(
        self,
        current_timestamp: float,
        upstream_materialization_timestamps: Mapping[AssetKey, Optional[float]],
    ) -> bool:
        return all(
            self._constraint.is_passing(current_timestamp, upstream_timestamp)
            for upstream_timestamp in upstream_materialization_timestamps.values()
        )


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
