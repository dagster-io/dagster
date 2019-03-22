from dagster_airflow.cli import create_dagster_airflow_cli


def test_init_cli():
    assert create_dagster_airflow_cli()
