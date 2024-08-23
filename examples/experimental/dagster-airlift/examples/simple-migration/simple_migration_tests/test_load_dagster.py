def test_defs_loads(airflow_instance) -> None:
    from simple_migration.dagster_defs.migrate import defs

    assert defs

    from simple_migration.dagster_defs.observe import defs

    assert defs

    from simple_migration.dagster_defs.peer import defs

    assert defs
