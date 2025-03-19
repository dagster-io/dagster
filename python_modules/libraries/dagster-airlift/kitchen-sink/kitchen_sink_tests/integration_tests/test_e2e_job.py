import pytest

from kitchen_sink_tests.integration_tests.conftest import makefile_dir


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> list[str]:
    return ["make", "run_dagster_jobs", "-C", str(makefile_dir())]


def test_run(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that when an asset fails and the run has the "RETRY_ON_ASSET_OR_OP_FAILURE_TAG" set to False,
    that the dag run fails.
    """
    banana = "ehllo"
    banana
