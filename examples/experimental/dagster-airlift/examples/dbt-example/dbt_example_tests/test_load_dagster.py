def test_defs_loads(airflow_instance):
    from dbt_example.dagster_defs import defs

    assert defs
