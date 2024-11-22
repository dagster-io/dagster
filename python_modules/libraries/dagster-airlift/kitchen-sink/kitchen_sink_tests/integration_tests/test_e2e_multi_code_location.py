from typing import List

import pytest
from dagster import AssetKey

from kitchen_sink_tests.integration_tests.conftest import (
    ExpectedMat,
    makefile_dir,
    poll_for_expected_mats,
)


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> list[str]:
    return ["make", "run_dagster_multi_code_locations", "-C", str(makefile_dir())]


def test_multiple_code_locations_materialize(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets can load properly, and that materializations register across multiple code locations."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()

    expected_mats_per_dag = {
        "dag_first_code_location": [
            ExpectedMat(AssetKey("dag_first_code_location__asset"), runs_in_dagster=False)
        ],
        "dag_second_code_location": [
            ExpectedMat(AssetKey("dag_first_code_location__asset"), runs_in_dagster=False)
        ],
    }

    poll_for_expected_mats(af_instance, expected_mats_per_dag)
