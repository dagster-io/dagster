import datetime
from contextlib import contextmanager

import packaging.version
import pendulum
from typing_extensions import TypeAlias

_IS_PENDULUM_2 = (
    hasattr(pendulum, "__version__")
    and getattr(packaging.version.parse(getattr(pendulum, "__version__")), "major") == 2
)


@contextmanager
def mock_pendulum_timezone(override_timezone):
    if _IS_PENDULUM_2:
        with pendulum.tz.test_local_timezone(pendulum.tz.timezone(override_timezone)):
            yield
    else:
        with pendulum.tz.LocalTimezone.test(pendulum.Timezone.load(override_timezone)):
            yield


def create_pendulum_time(year, month, day, *args, **kwargs):
    if "tz" in kwargs and "dst_rule" in kwargs and not _IS_PENDULUM_2:
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

    return (
        pendulum.datetime(year, month, day, *args, **kwargs)
        if _IS_PENDULUM_2
        else pendulum.create(year, month, day, *args, **kwargs)
    )


PendulumDateTime: TypeAlias = (
    pendulum.DateTime if _IS_PENDULUM_2 else pendulum.Pendulum  # type: ignore[attr-defined]
)


# Workaround for issue with .in_tz() in pendulum:
# https://github.com/sdispater/pendulum/issues/535
def to_timezone(dt: PendulumDateTime, tz: str):
    return pendulum.from_timestamp(dt.timestamp(), tz=tz)
