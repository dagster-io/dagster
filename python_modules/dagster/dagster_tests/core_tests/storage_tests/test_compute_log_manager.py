from dagster.core.test_utils import instance_for_test


def test_compute_log_manager_instance():
    with instance_for_test() as instance:
        assert instance.compute_log_manager
        assert instance.compute_log_manager._instance  # pylint: disable=protected-access
