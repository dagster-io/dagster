import datetime
from contextlib import contextmanager
from typing import Iterator, Optional, Union, cast

import packaging.version
import pendulum
import pendulum.parser
import pendulum.tz
from typing_extensions import Final, Protocol, Self, runtime_checkable

import dagster._check as check

# We support both pendulum 1.x and 2.x. 2.x renamed some core functionality-- specifically,
# `pendulum.Pendulum` became `pendulum.DateTime`. To make sure we maintain compatibility and to
# avoid choking type checkers (which lack a way to dynamically resolve a symbol depending on the
# environment), we use this module as a universal interface over `pendulum` 1 and 2.
#
# It replicates the APIs of pendulum that we use, but checks the installed version of pendulum
# and dispatches calls appropriately. Because we can't use Pendulum 2 objects in our type
# annotations, we instead use standins `PendulumDateTime` and `PendulumTimeZone` that stub the
# subset of the Pendulum APIs we use. Since we are explicitly stubbing every Pendulum API we use,
# modifications that tap as-yet-untapped APIs need to modify this module with the appropriate stubs.

_IS_PENDULUM_2: Final[bool] = (
    hasattr(pendulum, "__version__")
    and getattr(packaging.version.parse(getattr(pendulum, "__version__")), "major") == 2
)

# ########################
# ##### DATETIME INTERFACE
# ########################

# The real pendulum datetime class in both 1.x and 2.x subclasses `datetime.datetime`.
# `IPendulumDateTime` is where all pendulum-specific (not defined on `datetime.datetime`) methods
# should be stubbed.


@runtime_checkable
class IPendulumDateTime(Protocol):
    @property
    def timezone(self) -> Optional["PendulumTimeZone"]:
        ...

    def add(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> Self:  # type: ignore  # fmt: skip
        ...

    def subtract(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> Self:  # type: ignore  # fmt: skip
        ...

    def replace(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: Optional[int] = None,
        microsecond: Optional[int] = None,
    ) -> Self:  # type: ignore  # fmt: skip
        ...

    @property
    def int_timestamp(self) -> int:
        ...

    @property
    def float_timestamp(self) -> float:
        ...


# Type-ignored because Pyright complains that this class doesn't implement all members of the
# `IPendulumDateTime` protocol. However, we only ever cast real pendulum datetime objects as
# this class, so this doesn't need to implement anything.
class PendulumDateTime(datetime.datetime, IPendulumDateTime):  # type: ignore
    pass


@runtime_checkable
class IPendulumTimeZone(Protocol):
    @property
    def name(self) -> str:
        ...


# See `PendulumDateTime` for reason of type-ignore.
class PendulumTimeZone(datetime.tzinfo, IPendulumTimeZone):  # type: ignore
    pass


# type-ignore because pendulum.UTC is defined under both pendulum 1 and 2, but it's not properly public.
UTC = cast(PendulumTimeZone, pendulum.UTC)  # type: ignore

# ########################
# ##### FUNCTIONS
# ########################


def now(tz: Optional[Union[str, PendulumTimeZone]] = None) -> PendulumDateTime:
    # type-ignored because we pass a proxy `PendulumTimeZone` instance that `pendulum` doesn't
    # understand, but it's actually a real pendulum timezone object.
    return cast(PendulumDateTime, pendulum.now(tz))  # type: ignore


def instance(dt: datetime.datetime, tz: Optional[str] = None) -> PendulumDateTime:
    return cast(PendulumDateTime, pendulum.instance(dt, tz=tz))


def from_timestamp(timestamp: float, tz: str) -> PendulumDateTime:
    return cast(PendulumDateTime, pendulum.from_timestamp(timestamp, tz=tz))


def parse(dt: str, strict: bool = False) -> PendulumDateTime:
    return cast(PendulumDateTime, pendulum.parser.parse(dt, strict=strict))


def create_pendulum_time(
    year: int, month: int, day: int, *args: object, **kwargs: object
) -> PendulumDateTime:
    fn_name = "datetime" if _IS_PENDULUM_2 else "create"
    return cast(PendulumDateTime, getattr(pendulum, fn_name)(year, month, day, *args, **kwargs))


# Workaround for issues with .in_tz() in pendulum:
# https://github.com/sdispater/pendulum/issues/535
def to_timezone(dt: datetime.datetime, tz: str) -> PendulumDateTime:
    check.inst_param(dt, "dt", datetime.datetime)
    return cast(PendulumDateTime, pendulum.from_timestamp(dt.timestamp(), tz=tz))


def timezone(tz: str) -> PendulumTimeZone:
    return cast(PendulumTimeZone, pendulum.tz.timezone(tz))


@contextmanager
def test(dt: PendulumDateTime) -> Iterator[None]:
    # Everything type-ignored here because one of these branches will fail type-checking depending
    # on the version of pendulum installed.
    if _IS_PENDULUM_2:
        from pendulum.helpers import test as ptest  # type: ignore
    else:
        from pendulum import test as ptest  # type: ignore
    with ptest(dt):  # type: ignore
        yield


@contextmanager
def mock_pendulum_timezone(override_timezone: str) -> Iterator[None]:
    # Everything type-ignored here because one of these branches will fail type-checking depending
    # on the version of pendulum installed.
    if _IS_PENDULUM_2:
        from pendulum.tz.local_timezone import test_local_timezone  # type: ignore

        with test_local_timezone(pendulum.tz.timezone(override_timezone)):  # type: ignore
            yield
    else:
        with pendulum.tz.LocalTimezone.test(  # type: ignore
            pendulum.Timezone.load(override_timezone)  # type: ignore
        ):
            yield
