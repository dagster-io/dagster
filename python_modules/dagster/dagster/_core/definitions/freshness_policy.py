from abc import ABC, abstractmethod
from datetime import datetime
from typing import Mapping, Optional, Sequence, Tuple

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
        upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Optional[float]:
        raise NotImplementedError()

    @abstractmethod
    def constraints_for_time_window(
        self,
        window_start: datetime,
        window_end: datetime,
        upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Sequence[Tuple[AssetKey, datetime, datetime]]:
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

    def constraints_for_time_window(
        self,
        window_start: datetime,
        window_end: datetime,
        upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Sequence[Tuple[AssetKey, datetime, datetime]]:

        constraints = []
        period = pendulum.period(window_start, window_end)
        print(".................")
        print(upstream_materialization_times)
        print(period)
        print(window_start, window_end)

        # a MinimumFreshnessPolicy corresponds to an infinite series of constraints, as at
        # each point in time, the upstream materialization time of a given parent asset must
        # be no more than N minutes before that point in time.
        #
        # we interpolate this infinite series with to approximate it, keeping only the first fifty
        # distinct times to keep things manageable
        total_times = 0
        for time in period.range("minutes", self.minimum_freshness_minutes / 10.0):
            # add a constraint for each upstream key
            required_materialization_time = time - pendulum.duration(
                minutes=self.minimum_freshness_minutes
            )
            constraints.extend(
                [
                    (key, required_materialization_time, time)
                    for key, actual_time in upstream_materialization_times.items()
                    # remove constraints that have already been addressed based off of current data
                    if actual_time is None or actual_time < required_materialization_time
                ]
            )
            total_times += 1
            if total_times > 50:
                break

        return constraints

    def minutes_late(
        self,
        evaluation_time: datetime,
        upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Optional[float]:
        minimum_time = evaluation_time - pendulum.duration(minutes=self.minimum_freshness_minutes)

        minutes_late = 0.0
        for upstream_time in upstream_materialization_times.values():
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

    def constraints_for_time_window(
        self,
        window_start: datetime,
        window_end: datetime,
        upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Sequence[Tuple[AssetKey, datetime, datetime]]:

        constraints = []
        schedule_ticks = croniter(self.cron_schedule, window_start, ret_type=datetime)
        # iterate over each schedule tick in the provided time window
        current_tick = next(schedule_ticks)
        while current_tick < window_end:
            # add a constraint for each upstream key
            required_materialization_time = current_tick - pendulum.duration(
                self.minimum_freshness_minutes
            )
            constraints.extend(
                [
                    (key, required_materialization_time, current_tick)
                    for key, actual_time in upstream_materialization_times.items()
                    if actual_time is None or actual_time < required_materialization_time
                ]
            )
            current_tick = next(schedule_ticks)
        return constraints

    def minutes_late(
        self,
        evaluation_time: datetime,
        upstream_materialization_times: Mapping[AssetKey, Optional[datetime]],
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
        for upstream_materialization_time in upstream_materialization_times.values():

            # if any upstream materialization data is missing, then exit early
            if upstream_materialization_time is None:
                return None

            if upstream_materialization_time < latest_required_tick:
                # find the difference between the actual data time and the latest time that you would
                # have expected to get this data by
                expected_by_time = latest_required_tick + minimum_freshness_duration
                minutes_late = max(
                    minutes_late, (evaluation_time - expected_by_time).total_seconds() / 60
                )

        return minutes_late
