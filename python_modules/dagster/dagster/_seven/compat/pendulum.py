import datetime
from contextlib import contextmanager

import packaging.version
import pendulum
from typing_extensions import TypeAlias

_IS_PENDULUM_2_OR_NEWER = (
    hasattr(pendulum, "__version__")
    and getattr(packaging.version.parse(getattr(pendulum, "__version__")), "major") >= 2
)

_IS_PENDULUM_3_OR_NEWER = (
    hasattr(pendulum, "__version__")
    and getattr(packaging.version.parse(getattr(pendulum, "__version__")), "major") >= 3
)


PRE_TRANSITION = pendulum.tz.PRE_TRANSITION if _IS_PENDULUM_3_OR_NEWER else pendulum.PRE_TRANSITION
POST_TRANSITION = pendulum.tz.POST_TRANSITION if _IS_PENDULUM_3_OR_NEWER else pendulum.POST_TRANSITION
TRANSITION_ERROR = pendulum.tz.TRANSITION_ERROR if _IS_PENDULUM_3_OR_NEWER else pendulum.TRANSITION_ERROR


@contextmanager
def mock_pendulum_timezone(override_timezone):
    if _IS_PENDULUM_2_OR_NEWER:
        with pendulum.tz.test_local_timezone(pendulum.tz.timezone(override_timezone)):
            yield
    else:
        with pendulum.tz.LocalTimezone.test(pendulum.Timezone.load(override_timezone)):
            yield


@contextmanager
def pendulum_test(mock):
    if _IS_PENDULUM_3_OR_NEWER:
        with pendulum.travel_to(mock, freeze=True):
            yield
    else:
        with pendulum.test(mock):
            yield


def create_pendulum_time(year, month, day, *args, **kwargs):
    # pendulum <2.0
    if not _IS_PENDULUM_2_OR_NEWER:
        if "tz" in kwargs and "dst_rule" in kwargs:
            tz = pendulum.timezone(kwargs.pop("tz"))
            dst_rule = kwargs.pop("dst_rule")

            return pendulum.instance(
                tz.convert(
                    datetime.datetime(
                        year,
                        month,
                        day,
                        *args,
                        **kwargs,
                    ),
                    dst_rule=dst_rule,
                )
            )
        else:
            pendulum.create(year, month, day, *args, **kwargs)

    # pendulum >=3.0
    elif _IS_PENDULUM_3_OR_NEWER:
        raise_on_unknown_times = False
        fold = 1

        if "dst_rule" in kwargs:
            dst_rule = kwargs.pop("dst_rule")
            raise_on_unknown_times = (dst_rule == TRANSITION_ERROR)
            if dst_rule == PRE_TRANSITION:
                fold = 0
            elif dst_rule == POST_TRANSITION:
                fold = 1

        return pendulum.datetime(
            year,
            month,
            day,
            *args,
            fold=fold,
            raise_on_unknown_times=raise_on_unknown_times,
            **kwargs,
        )

    # pendulum >=2.0,<3.0
    else:
        return pendulum.datetime(year, month, day, *args, **kwargs)


def create_pendulum_timezone(*args, **kwargs):
    if _IS_PENDULUM_3_OR_NEWER:
        return pendulum.timezone(*args, **kwargs)
    else:
        return pendulum.tz.timezone(*args, **kwargs)


PendulumDateTime: TypeAlias = (
    pendulum.DateTime if _IS_PENDULUM_2_OR_NEWER else pendulum.Pendulum  # type: ignore[attr-defined]
)

Period: TypeAlias = pendulum.Interval if _IS_PENDULUM_3_OR_NEWER else pendulum.Period  # type: ignore[attr-defined]


# Workaround for issue with .in_tz() in pendulum:
# https://github.com/sdispater/pendulum/issues/535
def to_timezone(dt: PendulumDateTime, tz: str):
    timestamp = dt.timestamp()
    # handle negative timestamps, which are not natively supported on Windows
    if timestamp < 0:
        return pendulum.from_timestamp(0, tz=tz) + datetime.timedelta(seconds=timestamp)
    return pendulum.from_timestamp(dt.timestamp(), tz=tz)
