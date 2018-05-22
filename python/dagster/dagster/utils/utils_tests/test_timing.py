import pytest

from dagster.utils.timing import (time_execution_scope, TimerResult)


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
