from feature_graph_backed_assets import feature_graph_backed_assets

from dagster._core.test_utils import instance_for_test


def test_feature_graph_backed_assets():
    with instance_for_test() as instance:
        assert (
            feature_graph_backed_assets.get_job("airline_job")
            .execute_in_process(instance=instance)
            .success
        )
