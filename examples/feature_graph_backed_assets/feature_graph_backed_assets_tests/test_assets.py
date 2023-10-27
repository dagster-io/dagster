from dagster._core.test_utils import instance_for_test

from feature_graph_backed_assets import defs


def test_feature_graph_backed_assets():
    with instance_for_test() as instance:
        assert defs.get_job_def("airline_job").execute_in_process(instance=instance).success
