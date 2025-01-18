from dagster import Definitions


def test_peer_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.peer import defs

    assert defs

    Definitions.validate_loadable(defs)

    # representation of dag
    assert len(defs.get_all_asset_specs()) == 1


def test_observe_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.observe import defs

    assert defs

    Definitions.validate_loadable(defs)

    # representation of dag + 9 assets
    assert len(defs.get_all_asset_specs()) == 10


def test_migrate_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.migrate import defs

    assert defs

    Definitions.validate_loadable(defs)

    # representation of dag + 9 assets
    assert len(defs.get_all_asset_specs()) == 10


def test_standalone_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.stages.standalone import defs

    assert defs

    Definitions.validate_loadable(defs)

    # 1 fewer, since no representation of the overall DAG
    assert len(defs.get_all_asset_specs()) == 9
