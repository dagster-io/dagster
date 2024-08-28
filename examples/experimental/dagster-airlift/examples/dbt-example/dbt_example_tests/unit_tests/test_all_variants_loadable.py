from dbt_example.dagster_defs.constants import AIRFLOW_BASE_URL


def test_inclusion() -> None:
    assert AIRFLOW_BASE_URL
