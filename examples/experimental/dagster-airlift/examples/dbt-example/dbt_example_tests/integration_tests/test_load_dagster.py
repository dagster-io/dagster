def test_defs_loads(airflow_instance) -> None:
    from dbt_example.dagster_defs.peer import defs

    assert defs
    from dbt_example.dagster_defs.observe import defs

    assert defs
    from dbt_example.dagster_defs.migrate import defs

    assert defs
