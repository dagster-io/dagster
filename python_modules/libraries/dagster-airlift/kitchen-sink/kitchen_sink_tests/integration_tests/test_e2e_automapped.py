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
    return ["make", "run_dagster_automapped", "-C", str(makefile_dir())]


def ak(key: str) -> AssetKey:
    return AssetKey.from_user_string(key)


expected_mats_per_dag = {
    "print_dag": [
        ExpectedMat(AssetKey("the_print_asset"), runs_in_dagster=False),
        ExpectedMat(
            ak("my_airflow_instance/dag/print_dag/task/downstream_print_task"),
            runs_in_dagster=False,
        ),
        ExpectedMat(ak("my_airflow_instance/dag/print_dag/task/print_task"), runs_in_dagster=False),
    ],
}


def test_dagster_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets can load properly, and that materializations register."""
    from kitchen_sink.airflow_instance import local_airflow_instance

    af_instance = local_airflow_instance()
    poll_for_expected_mats(af_instance, expected_mats_per_dag)
