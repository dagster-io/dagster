from dagster import file_relative_path
from dagster.core.instance.config import dagster_instance_config
from dagster.utils.yaml_utils import load_yaml_from_globs


def test_yaml_schema():
    dagster_yaml_folder = file_relative_path(__file__, "../../../docs_snippets/overview/instances/")

    res = dagster_instance_config(dagster_yaml_folder)

    assert sorted(list(res.keys())) == [
        "compute_logs",
        "event_log_storage",
        "local_artifact_storage",
        "run_launcher",
        "run_storage",
        "schedule_storage",
        "scheduler",
    ]

    res = load_yaml_from_globs(
        file_relative_path(__file__, "../../../docs_snippets/overview/instances/pipeline_run.yaml")
    )

    assert res == {
        "execution": {"multiprocess": {"config": {"max_concurrent": 4}}},
        "storage": {"filesystem": None},
        "loggers": {"console": {"config": {"log_level": "DEBUG"}}},
    }
