def test_defs_loads(airflow_instance):
    from tutorial_example.dagster_defs import defs

    assert defs
