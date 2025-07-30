from dagster._core.test_utils import instance_for_test

from feature_graph_backed_assets.definitions import defs


def test_feature_graph_backed_assets() -> None:
    with instance_for_test() as instance:
        assert defs.resolve_job_def("airline_job").execute_in_process(instance=instance).success
