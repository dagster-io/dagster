from abc import ABC, abstractmethod
from typing import Mapping, Optional

import pendulum
from croniter import croniter

from .events import AssetKey


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


class MinimumFreshnessPolicy(FreshnessPolicy):
    """A freshness policy which specifies that the upstream data that was used for the most recent
    asset materialization must have been materialized no more than `minimum_freshness_minutes` ago,
    relative to the current time.
    """

    def __init__(self, minimum_freshness_minutes: float):
        self._minimum_freshness_minutes = minimum_freshness_minutes

    @property
    def minimum_freshness_minutes(self) -> float:
        return self._minimum_freshness_minutes

    def minutes_late(
        self,
        current_timestamp: float,
        upstream_materialization_timestamps: Mapping[AssetKey, Optional[float]],
    ) -> Optional[float]:
        current_datetime = pendulum.from_timestamp(current_timestamp)

        minimum_freshness_duration = pendulum.duration(minutes=self.minimum_freshness_minutes)
        minimum_datetime = current_datetime - minimum_freshness_duration

        minutes_late = 0.0
        for upstream_materialization_timestamp in upstream_materialization_timestamps.values():
            # if any upstream materialization data is missing, then exit early
            if upstream_materialization_timestamp is None:
                return None

            upstream_datetime = pendulum.from_timestamp(upstream_materialization_timestamp)
            if upstream_datetime < minimum_datetime:
                minutes_late = max(minutes_late, (minimum_datetime - upstream_datetime).minutes)
        return minutes_late


class CronMinimumFreshnessPolicy(FreshnessPolicy):
    """A freshness policy which specifies that the upstream data that was used for the most recent
    asset materialization must have been materialized no more than `minimum_freshness_minutes` ago,
    relative to the most recent cron schedule tick.
    """

    def __init__(self, minimum_freshness_minutes: float, cron_schedule: str):
        self._minimum_freshness_minutes = minimum_freshness_minutes
        self._cron_schedule = cron_schedule

    @property
    def minimum_freshness_minutes(self) -> float:
        return self._minimum_freshness_minutes

    @property
    def cron_schedule(self) -> str:
        return self._cron_schedule

    def minutes_late(
        self,
        current_timestamp: float,
        upstream_materialization_timestamps: Mapping[AssetKey, Optional[float]],
    ) -> Optional[float]:
        current_datetime = pendulum.from_timestamp(current_timestamp)
        minimum_freshness_duration = pendulum.duration(minutes=self.minimum_freshness_minutes)

        # find the most recent schedule tick which is more than minimum_freshness_duration old,
        # i.e. the most recent schedule tick which could be failing this constraint
        schedule_ticks = croniter(
            self.cron_schedule, current_datetime, ret_type=pendulum.DateTime, is_prev=True
        )
        latest_required_tick = next(schedule_ticks)
        while latest_required_tick + minimum_freshness_duration > current_datetime:
            latest_required_tick = next(schedule_ticks)

        minutes_late = 0.0
        for upstream_materialization_timestamp in upstream_materialization_timestamps.values():

            # if any upstream materialization data is missing, then exit early
            if upstream_materialization_timestamp is None:
                return None

            upstream_datetime = pendulum.from_timestamp(upstream_materialization_timestamp)
            if upstream_datetime < latest_required_tick:
                # find the difference between the actual data time and the latest time that you would
                # have expected to get this data by
                expected_by_time = latest_required_tick + minimum_freshness_duration
                minutes_late = max(
                    minutes_late, current_datetime.diff(expected_by_time).in_minutes()
                )

        return minutes_late
