import inspect
import os
import shutil
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

import pytest
from dagster import AssetExecutionContext, materialize
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli.app import app
from dagster_dbt.core.resources_v2 import DbtCliResource
from dagster_dbt.dbt_project import DbtProject
from typer.testing import CliRunner

runner = CliRunner()


@contextmanager
def tmp_script(
    script_fn: Callable[[], Any],
    *,
    tmp_path: Path,
    dbt_project_dir: Path,
    packaged_project_dir: Optional[Path] = None,
) -> Iterator[Path]:
    source = textwrap.dedent(inspect.getsource(script_fn).partition("\n")[-1])
    source = source.format(project_dir=dbt_project_dir, packaged_project_dir=packaged_project_dir)

    tmp_script_path = tmp_path.joinpath("definitions.py")
    tmp_script_path.write_text(source)

    yield tmp_script_path


@pytest.mark.parametrize(
    "packaged_project_dir_name",
    [
        "",
        "dbt-project",
    ],
    ids=[
        "no package data",
        "with package data",
    ],
)
def test_prepare_for_deployment(
    dbt_project_dir: Path, tmp_path: Path, packaged_project_dir_name: Optional[str]
) -> None:
    def script_fn() -> None:
        from dagster_dbt.dbt_project import DbtProject

        _ = DbtProject(
            project_dir="{project_dir}",
            packaged_project_dir="{packaged_project_dir}",
        )

    manifest_path = dbt_project_dir.joinpath("target", "manifest.json")
    packaged_project_dir = (
        tmp_path.joinpath(packaged_project_dir_name) if packaged_project_dir_name else None
    )

    with tmp_script(
        script_fn,
        tmp_path=tmp_path,
        dbt_project_dir=dbt_project_dir,
        packaged_project_dir=packaged_project_dir,
    ) as tmp_script_path:
        assert not manifest_path.exists()
        assert not packaged_project_dir or not packaged_project_dir.exists()

        result = runner.invoke(
            app,
            ["project", "prepare-for-deployment", "--file", os.fspath(tmp_script_path)],
        )

        assert result.exit_code == 0
        assert manifest_path.exists()
        assert not packaged_project_dir or packaged_project_dir.exists()


def test_prepare_for_deployment_with_state(
    monkeypatch: pytest.MonkeyPatch, dbt_project_dir: Path, tmp_path: Path
) -> None:
    monkeypatch.setenv("DAGSTER_DBT_JAFFLE_SCHEMA", "prod")

    def script_fn() -> None:
        from dagster_dbt.dbt_project import DbtProject

        _ = DbtProject(
            project_dir="{project_dir}",
            state_dir="prod_artifacts",
        )

    with tmp_script(
        script_fn, tmp_path=tmp_path, dbt_project_dir=dbt_project_dir
    ) as tmp_script_path:
        runner.invoke(
            app,
            ["project", "prepare-for-deployment", "--file", os.fspath(tmp_script_path)],
        )

    state_dir = dbt_project_dir.joinpath("prod_artifacts")
    state_dir.mkdir()

    project = DbtProject(dbt_project_dir, state_dir=state_dir.name)
    assert project.state_dir

    dbt = DbtCliResource(project)

    @dbt_assets(manifest=project.manifest_path)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        if os.getenv("DAGSTER_DBT_JAFFLE_SCHEMA") == "staging":
            assert dbt.get_defer_args()

        yield from dbt.cli(["build", *dbt.get_defer_args()], context=context).stream()

    # Running in production produces all the assets.
    result = materialize([my_dbt_assets], resources={"dbt": dbt})
    assert result.success

    # Running in staging should fail because the state directory is empty, so there is no --defer.
    monkeypatch.setenv("DAGSTER_DBT_JAFFLE_SCHEMA", "staging")
    result = materialize(
        [my_dbt_assets], selection="orders", resources={"dbt": dbt}, raise_on_error=False
    )
    assert not result.success

    # Once the state directory is populated, the subselected asset can be produced.
    shutil.copyfile(project.manifest_path, project.state_dir.joinpath("manifest.json"))

    with tmp_script(
        script_fn, tmp_path=tmp_path, dbt_project_dir=dbt_project_dir
    ) as tmp_script_path:
        runner.invoke(
            app,
            ["project", "prepare-for-deployment", "--file", os.fspath(tmp_script_path)],
        )

    result = materialize([my_dbt_assets], selection="orders", resources={"dbt": dbt})
    assert result.success
