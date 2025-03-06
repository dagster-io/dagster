from dagster import file_relative_path
from dagster._core.instance.config import dagster_instance_config


def test_dagster_yaml():
    dagster_yaml_folder = file_relative_path(
        __file__, "../../docs_snippets/deploying/docker/"
    )

    res, custom_instance_class = dagster_instance_config(
        dagster_yaml_folder, "dagster.yaml"
    )
    assert set(res.keys()) == {
        "storage",
        "compute_logs",
        "local_artifact_storage",
    }

    assert custom_instance_class is None
