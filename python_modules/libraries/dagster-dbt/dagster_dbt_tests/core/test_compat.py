import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


@pytest.mark.parametrize("dbt_version", [None, "2.0.0-beta.1", "2.0.0", "3.0.0"])
def test_import_without_dbt_core(tmp_path: Path, dbt_version: str | None) -> None:
    # A Fusion package may expose dbt.version without the dbt-core Python APIs.
    # Use a subprocess so the installed dbt-core and cached Dagster imports cannot mask this.
    dbt_package = tmp_path / "dbt"
    dbt_package.mkdir()
    dbt_package.joinpath("__init__.py").write_text(
        "raise ImportError('dbt-core is not installed')" if dbt_version is None else ""
    )
    if dbt_version is not None:
        dbt_package.joinpath("version.py").write_text(f"__version__ = {dbt_version!r}")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                from typing import Any
                from unittest.mock import patch

                import dagster_dbt
                from dagster_dbt.compat import (
                    DBT_PYTHON_VERSION, BaseAdapter, NodeType, NodeStatus, REFABLE_NODE_TYPES,
                )
                from dagster_dbt.utils import select_unique_ids

                assert DBT_PYTHON_VERSION is None
                assert BaseAdapter is Any
                assert NodeType.Model == "model"
                assert NodeStatus.Pass == "pass"
                assert REFABLE_NODE_TYPES == ["model", "seed", "snapshot"]

                project = object()
                with patch("dagster_dbt.utils._select_unique_ids_from_cli") as cli:
                    cli.return_value = {"model.project.example"}
                    assert select_unique_ids(
                        "tag:selected", "tag:excluded", "named_selector", project,
                        {"metadata": {"dbt_version": "2.0.0"}},
                    ) == {"model.project.example"}
                    cli.assert_called_once_with(
                        "tag:selected", "tag:excluded", "named_selector", project,
                    )
                """
            ),
        ],
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path), *sys.path])},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
