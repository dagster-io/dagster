from enum import Enum
from typing import Optional

import pendulum
from croniter import croniter


class AssetRootDataSLA:
    """For a given root data asset upstream of the asset which this SLA is applied to, specify a
    constraint on the timestamp of the materialization that was eventually consumed to produce the
    most recent materialization of this asset.
    """

    def is_passing(self, root_data_timestamp: Optional[float]) -> bool:
        pass


class StalenessSLA(AssetRootDataSLA):
    """This SLA specifies that an asset must not be materialized more than
    `allowed_staleness_minutes` after a given root asset.
    """

    def __init__(self, allowed_staleness_minutes: float):
        self._allowed_staleness = pendulum.duration(minutes=allowed_staleness_minutes)

    def is_passing(self, root_data_timestamp: Optional[float]) -> bool:
        if data_timestamp is None:
            return False

        return pendulum.from_timestamp(data_timestamp) > pendulum.now() - self._allowed_staleness


class CronSLA(AssetRootDataSLA):
    """This SLA specifies that an asset must not be materialized more than `allowed_staleness` time
    after each schedule tick.
    """

    def __init__(self, cron_schedule: str, allowed_staleness_minutes: float):
        self._cron_schedule = cron_schedule
        self._allowed_staleness = pendulum.duration(minutes=allowed_staleness_minutes)

    def is_passing(self, root_data_timestamp: Optional[float]) -> bool:
        if data_timestamp is None:
            return False

        now = pendulum.now()

        # find the most recent root data time that could possibly be missing its SLA
        data_times = croniter(self._cron_schedule, now, ret_type=pendulum.DateTime, is_prev=True)
        latest_data_time = next(data_times)
        while latest_data_time + self._allowed_staleness > now:
            latest_data_time = next(data_times)

        return pendulum.from_timestamp(data_timestamp) > latest_data_time
