from datetime import datetime
from typing import Mapping, NamedTuple, Optional

import pendulum
from croniter import croniter

import dagster._check as check
from dagster._annotations import experimental

from .events import AssetKey


@experimental
class FreshnessPolicy(
    NamedTuple(
        "_FreshnessPolicy",
        [
            ("maximum_lag_minutes", float),
            ("cron_schedule", Optional[str]),
        ],
    )
):
    """
    A FreshnessPolicy specifies how up-to-date you want a given asset to be, relative to the
    most recent available upstream data. At any point in time (or by each cron schedule tick, if
    cron_schedule is set), the data used to produce the current version of this asset must be no
    older than `maximum_lag_minutes` before the most recent available data.

    Examples:

        * `FreshnessPolicy(maximum_lag_minutes=30)`: At any point in time, this asset must
        incorporate all data from at least 30 minutes ago.
        * `FreshnessPolicy(maximum_lag_minutes=60, cron_schedule="0 1 * * *"): Every day by 1AM,
        this asset must incorporate all data from at least 60 minutes ago.
    """

    def __new__(cls, *, maximum_lag_minutes: float, cron_schedule: Optional[str] = None):
        return super(FreshnessPolicy, cls).__new__(
            cls,
            maximum_lag_minutes=float(
                check.numeric_param(maximum_lag_minutes, "maximum_lag_minutes")
            ),
            cron_schedule=check.opt_str_param(cron_schedule, "cron_schedule"),
        )

    def minutes_late(
        self,
        evaluation_time: Optional[datetime],
        used_data_times: Mapping[AssetKey, Optional[datetime]],
        available_data_times: Mapping[AssetKey, Optional[datetime]],
    ) -> Optional[float]:
        maximum_lag_duration = pendulum.duration(minutes=self.maximum_lag_minutes)

        if self.cron_schedule:
            # most recent cron schedule tick
            schedule_ticks = croniter(
                self.cron_schedule, evaluation_time, ret_type=datetime, is_prev=True
            )
            evaluation_tick = next(schedule_ticks)
        else:
            evaluation_tick = evaluation_time

        minutes_late = 0.0
        for asset_key, available_data_time in available_data_times.items():
            # upstream data is not available, undefined how out of date you are
            if available_data_time is None:
                return None

            # upstream data was not used, undefined how out of date you are
            used_data_time = used_data_times[asset_key]
            if used_data_time is None:
                return None

            # in the case that we're basing available data time off of upstream materialization
            # events instead of the current time, you are considered up to date if it's no more
            # than maximum_lag_duration after your upstream asset updated
            if (
                evaluation_time != available_data_time
                and evaluation_tick < available_data_time + maximum_lag_duration
            ):
                continue

            # require either the most recent available data time, or data from maximum_lag_duration
            # before the most recent evaluation tick, whichever is less strict
            required_time = min(available_data_time, evaluation_tick - maximum_lag_duration)

            if used_data_time < required_time:
                minutes_late = max(
                    minutes_late, (required_time - used_data_time).total_seconds() / 60
                )
        return minutes_late
