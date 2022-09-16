import pendulum
from croniter import croniter


class AssetSLA:
    def is_passing(self, data_timestamp: float):
        pass


class StalenessSLA(AssetSLA):
    """This SLA specifies that an asset must not be more than `allowed_staleness` time out of date
    at any point in time.
    """

    def __init__(self, allowed_staleness_minutes: float):
        self._allowed_staleness = pendulum.duration(minutes=allowed_staleness_minutes)

    def is_passing(self, data_timestamp: float) -> bool:
        if data_timestamp is None:
            return False

        return pendulum.from_timestamp(data_timestamp) > pendulum.now() - self._allowed_staleness


class CronSLA(AssetSLA):
    """This SLA specifies that a given asset must not be updated more than `allowed_staleness` time
    after each schedule tick.
    """

    def __init__(self, cron_schedule: str, allowed_staleness_minutes: float):
        self._cron_schedule = cron_schedule
        self._allowed_staleness = pendulum.duration(minutes=allowed_staleness_minutes)

    def is_passing(self, data_timestamp: float) -> bool:
        if data_timestamp is None:
            return False

        now = pendulum.now()

        # find the latest data time that could possibly be missing its SLA
        data_times = croniter(self._cron_schedule, now, ret_type=pendulum.DateTime, is_prev=True)
        latest_data_time = next(data_times)
        while latest_data_time + self._allowed_staleness > now:
            latest_data_time = next(data_times)

        return pendulum.from_timestamp(data_timestamp) > latest_data_time
