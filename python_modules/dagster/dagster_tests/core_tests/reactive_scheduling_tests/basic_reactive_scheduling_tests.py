from dagster._core.reactive_scheduling.scheduling_policy import SchedulingPolicy


def test_include_scheduling_policy() -> None:
    assert SchedulingPolicy
