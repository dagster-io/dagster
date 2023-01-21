from signal import Signals

from dagster._utils import get_run_crash_explanation, get_terminate_signal


def test_get_run_crash_explanation():
    assert get_run_crash_explanation("foo", 1) == "foo unexpectedly exited with code 1."
    assert (
        get_run_crash_explanation("foo", -Signals.SIGINT)
        == "foo was terminated by signal 2 (SIGINT)."
    )

    term_signal = get_terminate_signal()

    assert (
        f"foo was terminated by signal {term_signal} ({term_signal.name}). This usually"
        " indicates that the process was killed by the operating system due to running out of"
        " memory."
        in get_run_crash_explanation("foo", -get_terminate_signal())
    )
