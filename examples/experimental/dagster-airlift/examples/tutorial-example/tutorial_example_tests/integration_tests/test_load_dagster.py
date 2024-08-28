from dagster import AssetKey, Definitions


def test_migrate_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.migrate import defs

    assert defs

    Definitions.validate_loadable(defs)


def test_peer_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.peer import defs

    assert defs

    Definitions.validate_loadable(defs)

    assert len(defs.assets) == 1
    dag_asset = defs.assets[0]
    assert dag_asset.key == AssetKey(["airflow_instance", "dag", "rebuild_customers_list"])


def test_observe_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.observe import defs

    assert defs

    Definitions.validate_loadable(defs)

    assert len(defs.assets) == 4
    dag_asset = defs.assets[0]
    assert dag_asset.key == AssetKey(["airflow_instance", "dag", "rebuild_customers_list"])


def test_standalone_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.standalone import defs

    assert defs

    Definitions.validate_loadable(defs)
