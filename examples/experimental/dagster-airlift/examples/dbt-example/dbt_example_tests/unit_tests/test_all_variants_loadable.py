from pathlib import Path
from typing import Generator

import pytest
from dagster import Definitions
from dagster._core.test_utils import environ
from dbt_example.dagster_defs.constants import AIRFLOW_BASE_URL


@pytest.fixture
def dbt_project_dir() -> Generator[None, None, None]:
    with environ(
        {
            "DBT_PROJECT_DIR": str(
                Path(__file__).parent.parent.parent / "dbt_example" / "shared" / "dbt"
            )
        }
    ) as _:
        yield None


def test_inclusion(dbt_project_dir) -> None:
    """Include from dbt_example to ensure that nothing is broken module-wide."""
    assert AIRFLOW_BASE_URL


def test_complete(dbt_project_dir) -> None:
    """Test that loadable defs are valid."""
    from dbt_example.dagster_defs.complete import defs

    Definitions.validate_loadable(defs)
