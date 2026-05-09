import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import dagster as dg
import pytest
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from dagster_dbt_tests.dbt_projects import test_fusion_compatible_jaffle_shop_path


def test_package_root_imports_without_dbt_core() -> None:
    package_root = Path(__file__).resolve().parents[2]
    script = """
import builtins

real_import = builtins.__import__

def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "dbt" or name.startswith("dbt."):
        raise ModuleNotFoundError(name)
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = blocked_import

import dagster_dbt
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_dbt.compat import DBT_PYTHON_VERSION

assert dagster_dbt.__version__
assert DbtCliResource is not None
assert DbtProject is not None
assert dbt_assets is not None
assert DBT_PYTHON_VERSION is None
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [os.fspath(package_root), os.environ.get("PYTHONPATH", "")]
            ).rstrip(os.pathsep),
        },
    )

    assert result.returncode == 0, result.stderr


@pytest.fixture(name="project", scope="module")
def project_fixture() -> DbtProject:
    project = DbtProject(test_fusion_compatible_jaffle_shop_path)
    project.preparer.prepare(project)
    return project


@pytest.mark.fusion
@pytest.mark.parametrize("fail", [True, False])
def test_basic(project: DbtProject, fail: bool) -> None:
    @dbt_assets(manifest=project.manifest_path, project=project)
    def the_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
        if fail:
            yield from dbt.cli(
                ["build", "--vars", json.dumps({"break_customer_build": "true"})], context=context
            ).stream()
        else:
            yield from dbt.cli(["build"], context=context).stream()

    n_assets = len(list(the_assets.specs))
    n_checks = len(list(the_assets.check_specs))
    assert n_assets == 8
    assert n_checks == 20

    result = dg.materialize(
        [the_assets],
        resources={"dbt": DbtCliResource(project_dir=project.project_dir)},
        raise_on_error=not fail,
    )
    assert result.success == (not fail)

    n_materializations = len(result.get_asset_materialization_events())
    n_check_evaluations = len(result.get_asset_check_evaluations())
    if fail:
        # one asset fails, no materialization
        assert n_materializations == n_assets - 1
        # three checks on that asset, no check evaluations for them
        assert n_check_evaluations == n_checks - 3
    else:
        assert n_materializations == n_assets
        assert n_check_evaluations == n_checks


def test_select_unique_ids_raises_without_dbt_core_or_project() -> None:
    """Regression: dbt Cloud users without an adapter package (no dbt-core) must get a clear error."""
    from dagster_dbt.utils import select_unique_ids
    from dagster_shared.check import CheckError

    blocked = {
        "dbt": None,
        **{k: None for k in list(sys.modules) if k.startswith("dbt.")},
    }
    import dagster_dbt.compat as compat_mod

    with mock.patch.dict(sys.modules, blocked):
        importlib.reload(compat_mod)
        with mock.patch("dagster_dbt.utils.DBT_PYTHON_VERSION", None):
            with pytest.raises(CheckError, match="dbt-core is not installed"):
                select_unique_ids(
                    select="fqn:*",
                    exclude="",
                    selector="",
                    project=None,
                    manifest_json={},
                )

    # Restore compat module state so DBT_PYTHON_VERSION is not permanently None
    importlib.reload(compat_mod)
