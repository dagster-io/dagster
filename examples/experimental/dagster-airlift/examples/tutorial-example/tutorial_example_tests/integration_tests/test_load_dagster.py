import pytest
from dagster._core.definitions.definitions_class import Definitions


def test_defs_loads(airflow_instance) -> None:
    pytest.skip("Ben fixes in a follow-up PR")
    from tutorial_example.dagster_defs.definitions import defs

    assert defs

    Definitions.validate_loadable(defs)
