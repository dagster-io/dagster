from dagster._core.definitions.definitions_class import Definitions


def test_defs_loads(airflow_instance) -> None:
    from tutorial_example.dagster_defs.definitions import defs

    assert defs

    Definitions.validate_loadable(defs)
