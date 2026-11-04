from __future__ import annotations

import datetime as _datetime
import os
import re
import zoneinfo
from time import time
from typing import Any, Optional, Union

from dagster_cron import (
    DayMatching as _NativeDayMatching,
    DayOfWeekNumbering as _NativeDayOfWeekNumbering,
    NonexistentTimeBehavior as _NativeNonexistentTimeBehavior,
    Schedule as _NativeSchedule,
    ScheduleParts as _NativeScheduleParts,
)

UTC_DT = _datetime.timezone.utc
EPOCH = _datetime.datetime(1970, 1, 1)
MARKER = object()
OVERFLOW32B_MODE = False

MINUTE_FIELD = 0
HOUR_FIELD = 1
DAY_FIELD = 2
MONTH_FIELD = 3
DOW_FIELD = 4
SECOND_FIELD = 5
YEAR_FIELD = 6

UNIX_FIELDS = (MINUTE_FIELD, HOUR_FIELD, DAY_FIELD, MONTH_FIELD, DOW_FIELD)
SECOND_FIELDS = (MINUTE_FIELD, HOUR_FIELD, DAY_FIELD, MONTH_FIELD, DOW_FIELD, SECOND_FIELD)
YEAR_FIELDS = (
    MINUTE_FIELD,
    HOUR_FIELD,
    DAY_FIELD,
    MONTH_FIELD,
    DOW_FIELD,
    SECOND_FIELD,
    YEAR_FIELD,
)
CRON_FIELDS = {
    "unix": UNIX_FIELDS,
    "second": SECOND_FIELDS,
    "year": YEAR_FIELDS,
    len(UNIX_FIELDS): UNIX_FIELDS,
    len(SECOND_FIELDS): SECOND_FIELDS,
    len(YEAR_FIELDS): YEAR_FIELDS,
}
VALID_LEN_EXPRESSION = {key for key in CRON_FIELDS if isinstance(key, int)}


class CroniterError(ValueError):
    """General top-level Croniter base exception."""


class CroniterBadTypeRangeError(TypeError):
    """Raised when range inputs use incompatible types."""


class CroniterBadCronError(CroniterError):
    """Syntax, unknown value, or range error within a cron expression."""


class CroniterUnsupportedSyntaxError(CroniterBadCronError):
    """Valid cron syntax that is not supported by this implementation."""


class CroniterBadDateError(CroniterError):
    """Unable to find next/prev timestamp match."""


class CroniterNotAlphaError(CroniterBadCronError):
    """Cron syntax contains an invalid day or month abbreviation."""


def datetime_to_timestamp(value: _datetime.datetime) -> float:
    if value.tzinfo is not None:
        offset = value.utcoffset()
        if offset is None:
            raise ValueError("aware datetime returned no UTC offset")
        value = value.replace(tzinfo=None) - offset
    return (value - EPOCH).total_seconds()


def _timestamp_to_datetime(timestamp: float, tzinfo: Any = None) -> _datetime.datetime:
    if tzinfo is None:
        return EPOCH + _datetime.timedelta(seconds=timestamp)
    return _datetime.datetime.fromtimestamp(timestamp, tz=UTC_DT).astimezone(tzinfo)


def _timezone_key(value: _datetime.datetime) -> Optional[str]:
    tzinfo = value.tzinfo
    if tzinfo is None:
        return None

    for attr in ("key", "zone"):
        key = getattr(tzinfo, attr, None)
        if isinstance(key, str) and key:
            return key

    filename = getattr(tzinfo, "_filename", None)
    if isinstance(filename, str):
        marker = "zoneinfo/"
        if marker in filename:
            return filename.split(marker, 1)[1]
        zone_root = os.sep + "zoneinfo" + os.sep
        if zone_root in filename:
            return filename.split(zone_root, 1)[1]

    return None


def _as_zoneinfo_datetime(value: _datetime.datetime) -> _datetime.datetime:
    key = _timezone_key(value)
    if key is None:
        return value
    if isinstance(value.tzinfo, zoneinfo.ZoneInfo) and value.tzinfo.key == key:
        return value
    return _datetime.datetime.fromtimestamp(datetime_to_timestamp(value), zoneinfo.ZoneInfo(key))


def _coerce_start_time(
    start_time: Optional[Union[_datetime.datetime, float, int]],
) -> tuple[float, Any]:
    if start_time is None:
        return time(), None
    if isinstance(start_time, _datetime.datetime):
        return datetime_to_timestamp(start_time), start_time.tzinfo
    if isinstance(start_time, (float, int)):
        return float(start_time), None
    raise TypeError("start_time must be a datetime, float, int, or None")


def _ret_type_is_datetime(ret_type: type) -> bool:
    try:
        return issubclass(ret_type, _datetime.datetime)
    except TypeError as exc:
        raise TypeError("Invalid ret_type, only 'float' or 'datetime' is acceptable.") from exc


def _ret_type_is_float(ret_type: type) -> bool:
    try:
        return issubclass(ret_type, float)
    except TypeError as exc:
        raise TypeError("Invalid ret_type, only 'float' or 'datetime' is acceptable.") from exc


def _field_tokens(expr_format: str) -> list[str]:
    stripped = expr_format.strip()
    if not stripped:
        return []
    if stripped.startswith("@"):
        return [stripped]
    return stripped.split()


def _parts_mode(expr_format: str) -> Any:
    tokens = _field_tokens(expr_format)
    if len(tokens) == 5:
        return _NativeScheduleParts.FIVE
    if len(tokens) == 6:
        return _NativeScheduleParts.SIX
    if len(tokens) == 7:
        return _NativeScheduleParts.SEVEN
    return _NativeScheduleParts.ALL


def _native_expression(expr_format: str, second_at_beginning: bool) -> str:
    tokens = _field_tokens(expr_format)
    if second_at_beginning or len(tokens) not in {6, 7}:
        return expr_format
    if len(tokens) == 6:
        minute, hour, day, month, dow, second = tokens
        return " ".join([second, minute, hour, day, month, dow])
    minute, hour, day, month, dow, second, year = tokens
    return " ".join([second, minute, hour, day, month, dow, year])


def _default_precision(expr_format: str) -> int:
    return 60 if len(_field_tokens(expr_format)) == 5 else 1


def _question_mark_allowed_indexes(field_count: int, second_at_beginning: bool) -> set[int]:
    if field_count == 5 or not second_at_beginning:
        return {DAY_FIELD, DOW_FIELD}
    if field_count in {6, 7}:
        return {3, 5}
    return set()


def _validate_question_marks(expr_format: str, second_at_beginning: bool) -> None:
    tokens = _field_tokens(expr_format)
    if not tokens or tokens[0].startswith("@"):
        return
    allowed_indexes = _question_mark_allowed_indexes(len(tokens), second_at_beginning)
    for index, token in enumerate(tokens):
        if "?" not in token:
            continue
        if token != "?":
            raise CroniterBadCronError(
                f"[{expr_format}] is not acceptable. Question mark can not used with other characters"
            )
        if index not in allowed_indexes:
            raise CroniterBadCronError(
                f"[{expr_format}] is not acceptable. "
                "Question mark can only used in day_of_month or day_of_week"
            )


def _is_not_alpha_error(message: str) -> bool:
    if "not a valid month name" in message or "not a valid day-of-week name" in message:
        return True
    specified = re.search(r"'([^']+)' specified", message)
    if specified is None:
        return False
    token = specified.group(1)
    return token.isalpha() and token.lower() not in {"h", "r", "l", "w"}


def _croniter_parse_error(expr_format: str, exc: ValueError) -> CroniterBadCronError:
    message = str(exc)
    if _is_not_alpha_error(message):
        return CroniterNotAlphaError(f"[{expr_format.lower()}] is not acceptable")
    return CroniterBadCronError(message)


def _is_unreachable_day_of_month_error(exc: ValueError | CroniterBadCronError) -> bool:
    message = str(exc).lower()
    return (
        "day" in message
        and "month" in message
        and (
            "never" in message
            or "unreachable" in message
            or "can not occur" in message
            or "do not occur" in message
        )
    )


class _UnreachableScheduleIterator:
    def next(self):
        raise ValueError("failed to find next date")

    def previous(self):
        raise ValueError("failed to find previous date")


class _UnreachableSchedule:
    def iter(self, start_time=None):
        del start_time
        return _UnreachableScheduleIterator()

    def includes(self, moment):
        del moment
        return False


def _strict_year_token(strict_year) -> str | None:
    if strict_year is None:
        return None
    if isinstance(strict_year, (str, bytes)):
        return strict_year.decode() if isinstance(strict_year, bytes) else strict_year
    if isinstance(strict_year, int):
        return str(strict_year)
    try:
        return ",".join(str(int(year)) for year in strict_year)
    except TypeError:
        return str(int(strict_year))


def _expression_with_strict_year(
    expr_format: str,
    *,
    second_at_beginning: bool,
    strict_year=None,
) -> str:
    year_token = _strict_year_token(strict_year)
    if year_token is None:
        return expr_format

    tokens = _field_tokens(expr_format)
    if not tokens or tokens[0].startswith("@") or len(tokens) == 7:
        return expr_format
    if len(tokens) == 5:
        return " ".join([*tokens, "0", year_token])
    if len(tokens) == 6:
        return " ".join([*tokens, year_token])
    return expr_format


def _new_native_schedule(
    expr_format: str,
    *,
    day_or: bool = True,
    second_at_beginning: bool = False,
    search_years: int = 50,
) -> _NativeSchedule:
    _validate_question_marks(expr_format, second_at_beginning)
    return _NativeSchedule(
        _native_expression(expr_format, second_at_beginning),
        parts=_parts_mode(expr_format),
        day_matching=_NativeDayMatching.OR if day_or else _NativeDayMatching.AND,
        search_years=search_years,
        day_of_week_numbering=_NativeDayOfWeekNumbering.ZERO_INDEXED,
        wraparound_ranges=True,
        last_specifiers=True,
        nearest_weekday=True,
        nth_weekday_of_month=True,
        random_fields=True,
        nonexistent_time_behavior=_NativeNonexistentTimeBehavior.NEXT_EXISTENT,
    )


def _validate_with_core(
    expr_format: str,
    *,
    day_or: bool = True,
    second_at_beginning: bool = False,
    search_years: int = 50,
    strict_year=None,
) -> None:
    expression = _expression_with_strict_year(
        expr_format,
        second_at_beginning=second_at_beginning,
        strict_year=strict_year,
    )
    try:
        _new_native_schedule(
            expression,
            day_or=day_or,
            second_at_beginning=second_at_beginning,
            search_years=search_years,
        )
    except ValueError as exc:
        raise _croniter_parse_error(expr_format, exc) from exc


class croniter:
    MONTHS_IN_YEAR = 12
    RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6), (0, 59), (1970, 2099))
    ALPHACONV = ({}, {}, {"l": "l"}, {}, {}, {}, {})
    LOWMAP = ({}, {}, {0: 1}, {0: 1}, {7: 0}, {}, {})
    LEN_MEANS_ALL = (60, 24, 31, 12, 7, 60, 130)

    def __init__(
        self,
        expr_format: str,
        start_time: Optional[Union[_datetime.datetime, float]] = None,
        ret_type: type = float,
        day_or: bool = True,
        max_years_between_matches: Optional[int] = None,
        is_prev: bool = False,
        hash_id: Optional[Union[bytes, str]] = None,
        implement_cron_bug: bool = False,
        second_at_beginning: bool = False,
        expand_from_start_time: bool = False,
    ) -> None:
        if hash_id is not None and not isinstance(hash_id, (bytes, str)):
            raise TypeError("hash_id must be bytes or UTF-8 string")

        self._implement_cron_bug = implement_cron_bug
        self._expand_from_start_time = expand_from_start_time
        self._max_years_btw_matches_explicitly_set = max_years_between_matches is not None
        self._max_years_between_matches_value = max(int(max_years_between_matches or 50), 1)

        self.expr_format = expr_format
        self._ret_type = ret_type
        self._day_or = day_or
        self.second_at_beginning = bool(second_at_beginning)
        self._is_prev = is_prev
        self.tzinfo = None
        self.start_time = 0.0
        self.dst_start_time = 0.0
        self.cur = 0.0
        self.set_current(start_time, force=True)

        try:
            self._schedule = self._build_native_schedule()
        except CroniterBadCronError:
            raise
        except ValueError as exc:
            parse_error = _croniter_parse_error(expr_format, exc)
            if not _is_unreachable_day_of_month_error(parse_error):
                raise parse_error from exc
            self._schedule = _UnreachableSchedule()

        tokens = _field_tokens(expr_format)
        self.expressions = tokens
        self.nth_weekday_of_month: dict[int, set[int]] = {}
        self.nearest_weekday: list[int] = []
        self.fields = CRON_FIELDS.get(len(tokens), tuple(range(len(tokens))))

    @property
    def _max_years_between_matches(self) -> int:
        return self._max_years_between_matches_value

    @_max_years_between_matches.setter
    def _max_years_between_matches(self, value: int) -> None:
        self._max_years_between_matches_value = max(int(value), 1)
        if hasattr(self, "_schedule"):
            try:
                self._schedule = self._build_native_schedule()
            except CroniterBadCronError:
                raise
            except ValueError as exc:
                raise _croniter_parse_error(self.expr_format, exc) from exc

    @property
    def expanded(self):
        raise CroniterUnsupportedSyntaxError("croniter expanded state is not implemented")

    def _build_native_schedule(self):
        return _new_native_schedule(
            self.expr_format,
            day_or=self._day_or,
            second_at_beginning=self.second_at_beginning,
            search_years=self._max_years_between_matches,
        )

    @staticmethod
    def datetime_to_timestamp(value: _datetime.datetime) -> float:
        return datetime_to_timestamp(value)

    _datetime_to_timestamp = datetime_to_timestamp

    def timestamp_to_datetime(self, timestamp: float, tzinfo: Any = MARKER) -> _datetime.datetime:
        if tzinfo is MARKER:
            tzinfo = self.tzinfo
        return _timestamp_to_datetime(timestamp, tzinfo)

    _timestamp_to_datetime = timestamp_to_datetime

    def set_current(
        self, start_time: Optional[Union[_datetime.datetime, float, int]], force: bool = True
    ) -> float:
        if (force or self.cur is None) and start_time is not None:
            timestamp, tzinfo = _coerce_start_time(start_time)
            self.tzinfo = tzinfo
            self.start_time = timestamp
            self.dst_start_time = timestamp
            self.cur = timestamp
        elif force and start_time is None and self.cur == 0.0:
            self.start_time = time()
            self.dst_start_time = self.start_time
            self.cur = self.start_time
        return self.cur

    def get_current(self, ret_type=None):
        ret_type = ret_type or self._ret_type
        if _ret_type_is_datetime(ret_type):
            return self.timestamp_to_datetime(self.cur)
        if _ret_type_is_float(ret_type):
            return self.cur
        raise TypeError("Invalid ret_type, only 'float' or 'datetime' is acceptable.")

    def _native_start_time(self):
        start_time = self.timestamp_to_datetime(self.cur)
        return start_time if self.tzinfo is None else _as_zoneinfo_datetime(start_time)

    def _next_timestamp(self, is_prev: bool) -> float:
        try:
            iterator = self._schedule.iter(self._native_start_time())
            result = iterator.previous() if is_prev else iterator.next()
        except ValueError as exc:
            raise CroniterBadDateError(str(exc)) from exc
        return datetime_to_timestamp(result)

    def _get_next(self, ret_type=None, start_time=None, is_prev=None, update_current=None):
        if update_current is None:
            update_current = True
        if start_time is not None:
            self.set_current(start_time, force=True)
        if is_prev is None:
            is_prev = self._is_prev
        self._is_prev = is_prev

        ret_type = ret_type or self._ret_type
        as_datetime = _ret_type_is_datetime(ret_type)
        as_float = _ret_type_is_float(ret_type)
        if not as_datetime and not as_float:
            raise TypeError("Invalid ret_type, only 'float' or 'datetime' is acceptable.")

        result = self._next_timestamp(is_prev)
        if update_current:
            self.cur = result
        if as_datetime:
            return self.timestamp_to_datetime(result)
        return result

    def get_next(self, ret_type=None, start_time=None, update_current=True):
        if start_time is not None and self._expand_from_start_time:
            raise ValueError("start_time is not supported when using expand_from_start_time = True.")
        return self._get_next(ret_type=ret_type, start_time=start_time, is_prev=False, update_current=update_current)

    def get_prev(self, ret_type=None, start_time=None, update_current=True):
        return self._get_next(
            ret_type=ret_type, start_time=start_time, is_prev=True, update_current=update_current
        )

    def all_next(self, ret_type=None, start_time=None, update_current=None):
        try:
            while True:
                self._is_prev = False
                yield self._get_next(
                    ret_type=ret_type, start_time=start_time, update_current=update_current
                )
                start_time = None
        except CroniterBadDateError:
            if self._max_years_btw_matches_explicitly_set:
                return
            raise

    def all_prev(self, ret_type=None, start_time=None, update_current=None):
        try:
            while True:
                self._is_prev = True
                yield self._get_next(
                    ret_type=ret_type, start_time=start_time, update_current=update_current
                )
                start_time = None
        except CroniterBadDateError:
            if self._max_years_btw_matches_explicitly_set:
                return
            raise

    def iter(self, *args, **kwargs):
        del args, kwargs
        return self.all_prev if self._is_prev else self.all_next

    def __iter__(self):
        return self

    __next__ = next = _get_next

    @classmethod
    def match(
        cls,
        cron_expression,
        testdate,
        day_or=True,
        second_at_beginning=False,
        precision_in_seconds=None,
    ):
        return cls.match_range(
            cron_expression,
            testdate,
            testdate,
            day_or,
            second_at_beginning,
            precision_in_seconds,
        )

    @classmethod
    def match_range(
        cls,
        cron_expression,
        from_datetime,
        to_datetime,
        day_or=True,
        second_at_beginning=False,
        precision_in_seconds=None,
    ):
        if not isinstance(from_datetime, _datetime.datetime):
            from_datetime = _timestamp_to_datetime(float(from_datetime))
        if not isinstance(to_datetime, _datetime.datetime):
            to_datetime = _timestamp_to_datetime(float(to_datetime))

        try:
            cron = cls(
                cron_expression,
                to_datetime,
                ret_type=_datetime.datetime,
                day_or=day_or,
                second_at_beginning=second_at_beginning,
            )
            current = cron.get_current(_datetime.datetime)
            if not current.microsecond:
                current += _datetime.timedelta(microseconds=1)
            cron.set_current(current, force=True)
            previous = cron.get_prev()
        except ValueError:
            return False

        if precision_in_seconds is None:
            precision_in_seconds = _default_precision(cron_expression)
        duration = (to_datetime - from_datetime).total_seconds() + precision_in_seconds
        return (max(current, previous) - min(current, previous)).total_seconds() < duration

    @classmethod
    def expand(cls, expr_format, *args, **kwargs):
        if kwargs.get("strict", False):
            _validate_with_core(
                expr_format,
                second_at_beginning=kwargs.get("second_at_beginning", False),
                strict_year=kwargs.get("strict_year"),
            )
        cls(
            expr_format,
            hash_id=kwargs.get("hash_id"),
            second_at_beginning=kwargs.get("second_at_beginning", False),
        )
        raise CroniterUnsupportedSyntaxError("croniter expanded state is not implemented")

    @classmethod
    def is_valid(
        cls,
        expression,
        hash_id=None,
        encoding="UTF-8",
        second_at_beginning=False,
        **kwargs,
    ):
        del encoding
        strict = kwargs.get("strict", False)
        try:
            if strict:
                _validate_with_core(
                    expression,
                    second_at_beginning=second_at_beginning,
                    strict_year=kwargs.get("strict_year"),
                )
            else:
                cls(expression, hash_id=hash_id, second_at_beginning=second_at_beginning)
        except CroniterBadCronError as exc:
            if not strict and _is_unreachable_day_of_month_error(exc):
                return True
            return False
        return True


def croniter_range(
    start,
    stop,
    expr_format,
    ret_type=None,
    day_or=True,
    exclude_ends=False,
    _croniter=croniter,
    second_at_beginning=False,
    max_years_between_matches=None,
):
    if isinstance(start, _datetime.datetime) != isinstance(stop, _datetime.datetime):
        raise CroniterBadTypeRangeError("start and stop must be the same type")
    inferred_ret_type = _datetime.datetime if isinstance(start, _datetime.datetime) else float
    ret_type = ret_type or inferred_ret_type
    is_prev = stop < start
    iterator = _croniter(
        expr_format,
        start,
        ret_type=ret_type,
        day_or=day_or,
        is_prev=is_prev,
        second_at_beginning=second_at_beginning,
        max_years_between_matches=max_years_between_matches,
    )
    stop_cmp = (
        datetime_to_timestamp(stop)
        if ret_type is float and isinstance(stop, _datetime.datetime)
        else stop
    )

    if not exclude_ends and croniter.match(
        expr_format,
        start if isinstance(start, _datetime.datetime) else _timestamp_to_datetime(float(start)),
        day_or=day_or,
        second_at_beginning=second_at_beginning,
    ):
        yield start if ret_type is inferred_ret_type else iterator.get_current(ret_type)

    while True:
        try:
            candidate = iterator.get_prev(ret_type) if is_prev else iterator.get_next(ret_type)
        except CroniterBadDateError:
            return
        if is_prev:
            if candidate < stop_cmp or (exclude_ends and candidate == stop_cmp):
                return
        elif candidate > stop_cmp or (exclude_ends and candidate == stop_cmp):
            return
        yield candidate


__all__ = [
    "DAY_FIELD",
    "HOUR_FIELD",
    "MINUTE_FIELD",
    "MONTH_FIELD",
    "OVERFLOW32B_MODE",
    "SECOND_FIELD",
    "UTC_DT",
    "VALID_LEN_EXPRESSION",
    "YEAR_FIELD",
    "CroniterBadCronError",
    "CroniterBadDateError",
    "CroniterBadTypeRangeError",
    "CroniterError",
    "CroniterNotAlphaError",
    "CroniterUnsupportedSyntaxError",
    "croniter",
    "croniter_range",
    "datetime_to_timestamp",
]
