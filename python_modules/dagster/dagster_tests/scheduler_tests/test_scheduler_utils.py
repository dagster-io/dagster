MINUTE_BOUNDARY = 1670596320

from dagster._scheduler.scheduler import _get_next_scheduler_iteration_time


def test_next_iteration_time():
    assert MINUTE_BOUNDARY % 60 == 0

    assert _get_next_scheduler_iteration_time(MINUTE_BOUNDARY) == MINUTE_BOUNDARY + 60
    assert _get_next_scheduler_iteration_time(MINUTE_BOUNDARY + 0.01) == MINUTE_BOUNDARY + 60
    assert _get_next_scheduler_iteration_time(MINUTE_BOUNDARY + 30) == MINUTE_BOUNDARY + 60
    assert _get_next_scheduler_iteration_time(MINUTE_BOUNDARY + 59.99) == MINUTE_BOUNDARY + 60

    assert _get_next_scheduler_iteration_time(MINUTE_BOUNDARY + 60) == MINUTE_BOUNDARY + 120
