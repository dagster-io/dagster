from signal import Signals

from dagster._utils import get_run_crash_explanation


def test_get_run_crash_explanation():
    assert get_run_crash_explanation("foo", 1) == "foo unexpectedly exited with code 1."
    assert (
        get_run_crash_explanation("foo", -Signals.SIGTERM)
        == "foo was terminated by signal 15 (SIGTERM)."
    )
    assert (
        "foo was terminated by signal 9 (SIGKILL). This usually indicates that the process was"
        " killed by the operating system due to running out of memory."
        in get_run_crash_explanation("foo", -Signals.SIGKILL)
    )
