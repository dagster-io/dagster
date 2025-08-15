import pytest
import src.dagster_tutorial.defs

import dagster as dg


@pytest.fixture()
def defs():
    return dg.Definitions.merge(dg.components.load_defs(src.dagster_tutorial.defs))


def test_defs(defs):
    assert defs
