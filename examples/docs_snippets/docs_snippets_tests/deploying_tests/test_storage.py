from dagster import file_relative_path
from dagster.core.instance.config import dagster_instance_config


def test_dagster_pg_legacy_yaml():
    dagster_yaml_folder = file_relative_path(__file__, "../../docs_snippets/deploying/")

    res, _custom_instance_class = dagster_instance_config(
        dagster_yaml_folder, "dagster-pg-legacy.yaml"
    )
    assert set(res.keys()) == {"run_storage", "event_log_storage", "schedule_storage"}


def test_dagster_pg_yaml():
    dagster_yaml_folder = file_relative_path(__file__, "../../docs_snippets/deploying/")

    res, _custom_instance_class = dagster_instance_config(
        dagster_yaml_folder, "dagster-pg.yaml"
    )
    assert set(res.keys()) == {"storage"}
