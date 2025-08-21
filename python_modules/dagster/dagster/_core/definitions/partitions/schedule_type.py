from enum import Enum
from typing import Optional

import dagster._check as check
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class ScheduleType(Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    @property
    def ordinal(self):
        return {"HOURLY": 1, "DAILY": 2, "WEEKLY": 3, "MONTHLY": 4}[self.value]

    def __gt__(self, other: "ScheduleType") -> bool:
        check.inst_param(
            other, "other", ScheduleType, "Cannot compare ScheduleType with non-ScheduleType"
        )
        return self.ordinal > other.ordinal

    def __lt__(self, other: "ScheduleType") -> bool:
        check.inst_param(
            other, "other", ScheduleType, "Cannot compare ScheduleType with non-ScheduleType"
        )
        return self.ordinal < other.ordinal


def cron_schedule_from_schedule_type_and_offsets(
    schedule_type: ScheduleType,
    minute_offset: int,
    hour_offset: int,
    day_offset: Optional[int],
) -> str:
    if schedule_type is ScheduleType.HOURLY:
        return f"{minute_offset} * * * *"
    elif schedule_type is ScheduleType.DAILY:
        return f"{minute_offset} {hour_offset} * * *"
    elif schedule_type is ScheduleType.WEEKLY:
        return f"{minute_offset} {hour_offset} * * {day_offset if day_offset is not None else 0}"
    elif schedule_type is ScheduleType.MONTHLY:
        return f"{minute_offset} {hour_offset} {day_offset if day_offset is not None else 1} * *"
    else:
        check.assert_never(schedule_type)
