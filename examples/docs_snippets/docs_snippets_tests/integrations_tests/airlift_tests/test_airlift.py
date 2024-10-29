def test_installs():
    """Test dagster-airlift package and submodules can be installed, as well as tutorial-example."""
    import dagster_airlift
    import dagster_airlift.core
    import dagster_airlift.dbt
    import dagster_airlift.in_airflow
    import dagster_airlift.k8s
    import tutorial_example
