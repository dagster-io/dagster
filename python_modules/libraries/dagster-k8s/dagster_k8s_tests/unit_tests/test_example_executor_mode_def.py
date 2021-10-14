# start_marker
from dagster import ModeDefinition, default_executors, pipeline
from dagster_k8s import k8s_job_executor


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [k8s_job_executor])])
def k8s_pipeline():
    pass


# end_marker


def test_mode():
    assert k8s_pipeline
