from airline_assets.airline_repository import airline_repository

from dagster.core.test_utils import instance_for_test


def test_airline_assets():
    with instance_for_test() as instance:
        assert (
            airline_repository.get_job("airline_job").execute_in_process(instance=instance).success
        )
