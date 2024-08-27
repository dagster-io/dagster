# For some reason the buildkite job is not finding the manifest.json so skipping all these
import os
from pathlib import Path

import pytest
from dagster import AssetSpec, Definitions, multi_asset
from dagster_airlift.core import dag_defs, task_defs
from dagster_airlift.dbt.multi_asset import dbt_defs
from dagster_dbt import DbtProject
from tutorial_example.dagster_defs.build_dag_defs import build_dag_defs


def dbt_project_path() -> Path:
    return Path(__file__).parent / "dbt"


def duckdb_path() -> Path:
    return Path(__file__).parent / "jaffle_shop.duckdb"


def is_buildkite() -> bool:
    return "BUILDKITE" in os.environ


@pytest.mark.skipif(
    is_buildkite(), reason="Skipping because the buildkite job is not finding the manifest.json"
)
def test_loadable():
    dag_defs = build_dag_defs(
        duckdb_path=duckdb_path(),
        dbt_project_path=dbt_project_path(),
    )
    Definitions.validate_loadable(dag_defs)


@pytest.mark.skipif(
    is_buildkite(), reason="Skipping because the buildkite job is not finding the manifest.json"
)
def test_dbt_defs() -> None:
    defs = dbt_defs(
        manifest=dbt_project_path() / "target" / "manifest.json",
        project=DbtProject(dbt_project_path()),
    )

    Definitions.validate_loadable(defs)


@pytest.mark.skipif(
    is_buildkite(), reason="Skipping because the buildkite job is not finding the manifest.json"
)
def test_dbt_defs_in_task_defs() -> None:
    defs = dag_defs(
        "some_dag",
        task_defs(
            "build_dbt_models",
            dbt_defs(
                manifest=dbt_project_path() / "target" / "manifest.json",
                project=DbtProject(dbt_project_path()),
            ),
        ),
    )

    Definitions.validate_loadable(defs)


@pytest.mark.skipif(
    is_buildkite(), reason="Skipping because the buildkite job is not finding the manifest.json"
)
def test_dbt_defs_collision_minimal_repro() -> None:
    @multi_asset(specs=[AssetSpec(key="some_key")])
    def an_asset() -> None: ...

    defs = dag_defs(
        "some_dag",
        task_defs(
            "t1",
            dbt_defs(
                manifest=dbt_project_path() / "target" / "manifest.json",
                project=DbtProject(dbt_project_path()),
            ),
        ),
        task_defs(
            "t2",
            Definitions(assets=[an_asset]),
        ),
    )

    Definitions.validate_loadable(defs)
