import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
import requests
from airlift_federation_tutorial_tests.conftest import (
    ORIG_DEFS_FILE,
    SNIPPETS_DIR,
    makefile_dir,
    replace_file,
)
from dagster_airlift.in_airflow.gql_queries import ASSET_NODES_QUERY
from dagster_airlift.test.shared_fixtures import stand_up_dagster

OBSERVE_COMPLETE_FILE = ORIG_DEFS_FILE.parent / "stages" / "observe_complete.py"
OBSERVE_WITH_DEPS_FILE = ORIG_DEFS_FILE.parent / "stages" / "observe_with_deps.py"
OBSERVE_SNIPPETS_FILE = SNIPPETS_DIR / "observe.py"
EXECUTABLE_AND_DA_FILE = ORIG_DEFS_FILE.parent / "stages" / "executable_and_da.py"
FEDERATED_EXECUTION_SNIPPETS_FILE = SNIPPETS_DIR / "federated_execution.py"


@pytest.fixture
def stage_file(request: pytest.FixtureRequest) -> Path:
    return request.param


@pytest.fixture
def simulate_stage(stage_file: Path) -> Generator[None, None, None]:
    with replace_file(ORIG_DEFS_FILE, stage_file):
        yield


@pytest.fixture(name="dagster_dev")
def dagster_fixture(
    warehouse_airflow: subprocess.Popen, metrics_airflow: subprocess.Popen, simulate_stage: None
) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_dagster(
            dagster_dev_cmd=["make", "-C", str(makefile_dir()), "dagster_run"],
            port=3000,
        ) as process:
            yield process
    finally:
        if process:
            process.terminate()


@pytest.mark.parametrize(
    "stage_file",
    [
        OBSERVE_COMPLETE_FILE,
        OBSERVE_WITH_DEPS_FILE,
        OBSERVE_SNIPPETS_FILE,
        FEDERATED_EXECUTION_SNIPPETS_FILE,
        EXECUTABLE_AND_DA_FILE,
    ],
    indirect=True,
)
def test_stage(dagster_dev: subprocess.Popen, stage_file: Path) -> None:
    response = requests.post(
        # Timeout in seconds
        "http://localhost:3000/graphql",
        json={"query": ASSET_NODES_QUERY},
        timeout=3,
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["assetNodes"]) > 0
