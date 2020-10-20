import pytest
from dagster.utils.timing import TimerResult, format_duration, time_execution_scope


def test_format_duration():
    timing_pairs = [
        (0.0, "0.0ms"),
        (0.84123, "0.84ms"),
        (5.67822, "5.68ms"),
        (10.123, "10ms"),
        (533.12123, "533ms"),
        (4567.123123, "4.57s"),
        (320000.1232, "5m20s"),
        (3910056.123, "1h5m"),
        (9022312.1233, "2h30m"),
    ]

    for ms, time_str in timing_pairs:
        assert format_duration(ms) == time_str


def test_basic_usage():
    with time_execution_scope() as timer_result:
        pass

    assert timer_result
    assert isinstance(timer_result.millis, float)
    assert isinstance(timer_result.seconds, float)


def test_wrong_usage():
    with pytest.raises(Exception):
        timer_result = TimerResult()
        assert timer_result.millis

    with pytest.raises(Exception):
        timer_result = TimerResult()
        assert timer_result.seconds
