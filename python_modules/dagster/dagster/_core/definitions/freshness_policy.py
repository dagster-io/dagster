from abc import ABC, abstractmethod
from datetime import datetime
from typing import Mapping, Optional

import pendulum
from croniter import croniter

from dagster._annotations import experimental

from .events import AssetKey


@experimental
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
        evaluation_time: datetime,
        used_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
        latest_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
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

    @staticmethod
    def maximum_latency(allowed_latency_minutes: float) -> "MaximumLatencyFreshnessPolicy":
        """Static constructor for a freshness policy which specifies that this asset should
        incorporate the latest available upstream data no more than `allowed_latency_minutes` after
        that data is produced.
        """
        return MaximumLatencyFreshnessPolicy(allowed_latency_minutes=allowed_latency_minutes)


@experimental
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
        evaluation_time: datetime,
        used_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
        latest_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Optional[float]:
        minimum_time = evaluation_time - pendulum.duration(minutes=self.minimum_freshness_minutes)

        minutes_late = 0.0
        for upstream_time in used_upstream_materialization_times.values():
            # if any upstream materialization data is missing, then exit early
            if upstream_time is None:
                return None

            if upstream_time < minimum_time:
                minutes_late = max(
                    minutes_late, (minimum_time - upstream_time).total_seconds() / 60
                )
        return minutes_late


@experimental
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
        evaluation_time: datetime,
        used_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
        latest_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Optional[float]:
        minimum_freshness_duration = pendulum.duration(minutes=self.minimum_freshness_minutes)

        # find the most recent schedule tick which is more than minimum_freshness_duration old,
        # i.e. the most recent schedule tick which could be failing this constraint
        schedule_ticks = croniter(
            self.cron_schedule, evaluation_time, ret_type=datetime, is_prev=True
        )
        latest_required_tick = next(schedule_ticks)
        while latest_required_tick + minimum_freshness_duration > evaluation_time:
            latest_required_tick = next(schedule_ticks)

        minutes_late = 0.0
        for upstream_materialization_time in used_upstream_materialization_times.values():

            if (
                upstream_materialization_time is None
                or upstream_materialization_time < latest_required_tick
            ):
                # find the difference between the actual data time and the latest time that you would
                # have expected to get this data by
                expected_by_time = latest_required_tick + minimum_freshness_duration
                minutes_late = max(
                    minutes_late, (evaluation_time - expected_by_time).total_seconds() / 60
                )

        return minutes_late


@experimental
class MaximumLatencyFreshnessPolicy(FreshnessPolicy):
    """A freshness policy which specifies that this asset should incorporate the latest available
    upstream data no more than `allowed_latency_minutes` after that data is produced.
    """

    def __init__(self, allowed_latency_minutes: float):
        self._allowed_latency_minutes = allowed_latency_minutes

    @property
    def allowed_latency_minutes(self) -> float:
        return self._allowed_latency_minutes

    def minutes_late(
        self,
        evaluation_time: datetime,
        used_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
        latest_upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Optional[float]:
        allowed_latency_duration = pendulum.duration(minutes=self.allowed_latency_minutes)

        minutes_late = 0.0
        for (
            upstream_key,
            latest_available_time,
        ) in latest_upstream_materialization_times.items():

            # if upstream asset does not exist yet, then you're not out of date with respect to it
            if latest_available_time is None:
                continue

            # get the time of the materialization that was actually used
            used_time = used_upstream_materialization_times[upstream_key]

            # already incorporated the latest available time
            if used_time == latest_available_time:
                continue

            # expect to have incorporated this data within allowed_latency_duration
            expected_by_time = latest_available_time + allowed_latency_duration
            if evaluation_time > expected_by_time:
                minutes_late = max(
                    minutes_late, (evaluation_time - expected_by_time).total_seconds() / 60
                )

        return minutes_late
