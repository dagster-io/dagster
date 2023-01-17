from contextlib import contextmanager

import packaging.version
import pendulum

_IS_PENDULUM_2 = (
    hasattr(pendulum, "__version__")
    and getattr(packaging.version.parse(pendulum.__version__), "major")
    == 2  # pylint: disable=no-member
)


@contextmanager
def mock_pendulum_timezone(override_timezone):
    if _IS_PENDULUM_2:
        with pendulum.tz.test_local_timezone(  # pylint: disable=no-member
            pendulum.tz.timezone(override_timezone)  # pylint: disable=no-member
        ):
            yield
    else:
        with pendulum.tz.LocalTimezone.test(  # pylint: disable=no-member
            pendulum.Timezone.load(override_timezone)  # pylint: disable=no-member
        ):
            yield


def create_pendulum_time(year, month, day, *args, **kwargs):
    return (
        pendulum.datetime(  # pylint: disable=no-member, pendulum-create
            year, month, day, *args, **kwargs
        )
        if _IS_PENDULUM_2
        else pendulum.create(  # pylint: disable=no-member, pendulum-create
            year, month, day, *args, **kwargs
        )
    )


# pylint: disable=no-member
PendulumDateTime = (
    pendulum.DateTime if _IS_PENDULUM_2 else pendulum.Pendulum  # type: ignore[attr-defined]
)


# Workaround for issues with .in_tz() in pendulum:
# https://github.com/sdispater/pendulum/issues/535
def to_timezone(dt, tz):
    import dagster._check as check

    check.inst_param(dt, "dt", PendulumDateTime)
    return pendulum.from_timestamp(dt.timestamp(), tz=tz)
