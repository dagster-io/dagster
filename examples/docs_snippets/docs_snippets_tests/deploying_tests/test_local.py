from dagster import file_relative_path
from dagster.core.instance.config import dagster_instance_config


def test_dagster_yaml():
    dagster_yaml_folder = file_relative_path(__file__, "../../docs_snippets/deploying/docker/")

    res = dagster_instance_config(dagster_yaml_folder, "dagster.yaml")
    assert set(res.keys()) == {
        "schedule_storage",
        "local_artifact_storage",
        "compute_logs",
        "run_storage",
        "event_log_storage",
        "scheduler",
    }
