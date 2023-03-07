import logging
import os
import sys
from typing import List

import dagster._check as check
import pytest
from dagster_dbt.cli.utils import _create_command_list, execute_cli


def test_execute_cli_requires_dbt_installed(monkeypatch, test_project_dir, dbt_config_dir):
    monkeypatch.setitem(sys.modules, "dbt", None)

    with pytest.raises(check.CheckError):
        execute_cli(
            executable="dbt",
            command="ls",
            log=logging.getLogger(__name__),
            flags_dict={
                "project-dir": test_project_dir,
                "profiles-dir": dbt_config_dir,
                "select": "*",
                "resource-type": "model",
                "output": "json",
            },
            warn_error=False,
            ignore_handled_error=False,
            target_path=os.path.join(test_project_dir, "target"),
        )


@pytest.mark.parametrize(
    argnames=["debug", "prefix"],
    argvalues=[
        (True, ["dbt", "--debug"]),
        (False, ["dbt"]),
    ],
    ids=["debug", "no-debug"],
)
def test_create_command_list_debug(debug: bool, prefix: List[str]):
    command_list = _create_command_list(
        executable="dbt",
        warn_error=False,
        json_log_format=False,
        command="run",
        flags_dict={},
        debug=debug,
    )
    assert command_list == prefix + ["run"]
