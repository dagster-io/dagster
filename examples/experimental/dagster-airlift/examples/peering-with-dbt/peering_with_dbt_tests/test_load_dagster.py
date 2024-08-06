def test_defs_loads(airflow_instance):
    from peering_with_dbt.dagster_defs import defs

    assert defs
