import os
import subprocess

import pytest


def _dbt_command(cmd: str):
    """Run a dbt command within a specific project lesson dbt project."""
    dbt_dir = os.path.join(
        os.path.dirname(__file__),
        "../src/project_dbt/analytics",
    )

    cmd = ["dbt", cmd, "--project-dir", dbt_dir, "--profiles-dir", dbt_dir]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        pytest.fail(f"dbt command failed: {result.returncode}")


@pytest.fixture(scope="session", autouse=True)
def setup_dbt_env():
    """Run necessary dbt commands to generate the dbt manifest.json required for Dagster to parse."""
    _dbt_command("deps")
    _dbt_command("parse")
