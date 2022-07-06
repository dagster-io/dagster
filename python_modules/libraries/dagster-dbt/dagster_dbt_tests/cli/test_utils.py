import logging
import os
import sys

import pytest
from dagster_dbt.cli.utils import execute_cli

import dagster._check as check


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
