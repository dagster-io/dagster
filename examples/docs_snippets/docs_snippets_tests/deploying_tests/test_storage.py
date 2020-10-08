from dagster import file_relative_path
from dagster.core.instance.config import dagster_instance_config


def test_dagster_postgres_yaml():
    dagster_yaml_folder = file_relative_path(__file__, "../../docs_snippets/deploying/")

    res = dagster_instance_config(dagster_yaml_folder, "postgres_dagster.yaml")
    assert set(res.keys()) == {"run_storage", "event_log_storage"}


def test_dagster_pg_yaml():
    dagster_yaml_folder = file_relative_path(__file__, "../../docs_snippets/deploying/")

    res = dagster_instance_config(dagster_yaml_folder, "dagster-pg.yaml")
    assert set(res.keys()) == {"run_storage", "event_log_storage", "schedule_storage"}
