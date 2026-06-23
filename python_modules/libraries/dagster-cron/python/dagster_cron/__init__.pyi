from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from enum import Enum

class ScheduleParts(Enum):
    FIVE: int
    SIX: int
    SEVEN: int
    FIVE_OR_SIX: int
    SIX_OR_SEVEN: int
    ALL: int

class DayMatching(Enum):
    AND: int
    OR: int

class DayOfWeekNumbering(Enum):
    ONE_INDEXED: int
    ZERO_INDEXED: int

class NonexistentTimeBehavior(Enum):
    SKIP: int
    NEXT_EXISTENT: int

class Schedule:
    def __init__(
        self,
        expression: str,
        parts: ScheduleParts = ...,
        day_matching: DayMatching = ...,
        search_years: int | None = ...,
        day_of_week_numbering: DayOfWeekNumbering = ...,
        wraparound_ranges: bool = ...,
        last_specifiers: bool = ...,
        nearest_weekday: bool = ...,
        nth_weekday_of_month: bool = ...,
        random_fields: bool = ...,
        nonexistent_time_behavior: NonexistentTimeBehavior = ...,
    ) -> None: ...
    def source(self) -> str: ...
    def iter(self, start_time: dt.datetime | None = ...) -> ScheduleIterator: ...
    def includes(self, moment: dt.datetime) -> bool: ...

class ScheduleIterator:
    def current(self) -> dt.datetime: ...
    def next(self) -> dt.datetime: ...
    def previous(self) -> dt.datetime: ...
    def __iter__(self) -> ScheduleIterator: ...
    def __next__(self) -> dt.datetime: ...

class CronStringIterator(Iterator[dt.datetime]):
    def __iter__(self) -> CronStringIterator: ...
    def __next__(self) -> dt.datetime: ...

def cron_string_iterator(
    start_timestamp: float,
    cron_string: str,
    execution_timezone: str | None,
    ascending: bool = ...,
    start_offset: int = ...,
) -> CronStringIterator: ...
def is_valid_cron_string(cron_string: str) -> bool: ...
def repeats_every_hour(cron_string: str) -> bool: ...
