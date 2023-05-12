from typing import List

import pytest
from dagster_dbt.cli import DbtCli, DbtManifest

from ..conftest import TEST_PROJECT_DIR

pytest.importorskip("dbt.version", minversion="1.4")


manifest_path = f"{TEST_PROJECT_DIR}/manifest.json"
manifest = DbtManifest.read(path=manifest_path)


@pytest.mark.parametrize("global_config", [[], ["--debug"]])
@pytest.mark.parametrize("command", ["run", "parse"])
def test_dbt_cli(global_config: List[str], command: str) -> None:
    dbt = DbtCli(project_dir=TEST_PROJECT_DIR, global_config=global_config)
    dbt_cli_task = dbt.cli([command])

    dbt_cli_task.wait()

    assert dbt_cli_task.process.args == ["dbt", *global_config, command]
    assert dbt_cli_task.process.returncode == 0
