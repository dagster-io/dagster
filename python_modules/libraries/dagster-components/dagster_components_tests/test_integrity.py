def test_shim_integrity():
    from dagster_components.dagster_dbt import DbtProjectComponent  # noqa: F401
    from dagster_components.dagster_sling import SlingReplicationCollectionComponent  # noqa: F401
