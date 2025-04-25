# ruff: noqa: F841 TID252

import importlib
import inspect
import subprocess
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

import yaml
from dagster import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path, pushd
from dagster._utils.env import environ
from dagster.components import ComponentLoadContext
from dagster.components.core.context import use_component_load_context
from dagster.components.core.defs_module import get_component
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dlt import DltLoadCollectionComponent
from dagster_dlt.components.dlt_load_collection.component import DltLoadSpecModel
from dlt import Pipeline

from dagster_dlt_tests.dlt_test_sources.duckdb_with_transformer import pipeline as dlt_source

ensure_dagster_tests_import()
ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    install_editable_dagster_packages_to_venv,
    isolated_example_project_foo_bar,
)


@contextmanager
def _modify_yaml(path: Path) -> Iterator[dict[str, Any]]:
    with open(path) as f:
        data = yaml.safe_load(f)
    yield data  # modify data here
    with open(path, "w") as f:
        yaml.dump(data, f)


def dlt_init(source: str, dest: str) -> None:
    yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
    subprocess.check_call(["dlt", "init", source, dest], stdin=yes.stdout)


@contextmanager
def setup_dlt_component(
    load_py_contents: Callable, component_body: dict[str, Any], setup_dlt_sources: Callable
) -> Iterator[tuple[DltLoadCollectionComponent, Definitions]]:
    """Sets up a components project with a dlt component based on provided params."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        alter_sys_path(to_add=[str(Path.cwd() / "src")], to_remove=[]),
    ):
        install_editable_dagster_packages_to_venv(Path(".venv"), ["libraries/dagster-dlt"])

        defs_path = Path.cwd() / "src" / "foo_bar" / "defs"
        component_path = defs_path / "ingest"
        component_path.mkdir(parents=True, exist_ok=True)

        with pushd(str(component_path)):
            setup_dlt_sources()

        Path(component_path / "load.py").write_text(
            textwrap.dedent("\n".join(inspect.getsource(load_py_contents).split("\n")[1:]))
        )
        (component_path / "component.yaml").write_text(yaml.safe_dump(component_body))

        defs_root = importlib.import_module("foo_bar.defs.ingest")
        project_root = Path.cwd()

        context = ComponentLoadContext.for_module(defs_root, project_root)
        with use_component_load_context(context):
            component = get_component(context)
            assert isinstance(component, DltLoadCollectionComponent)
            yield component, component.build_defs(context)


def github_load():
    import dlt

    from .github import github_reactions  # type: ignore

    duckdb_repo_reactions_issues_only_source = github_reactions(
        "duckdb", "duckdb", items_per_page=100, max_items=100
    ).with_resources("issues")
    duckdb_repo_reactions_issues_only_pipeline = dlt.pipeline(
        "github_reactions",
        destination="snowflake",
        dataset_name="duckdb_issues",
    )


BASIC_GITHUB_COMPONENT_BODY = {
    "type": "dagster_dlt.DltLoadCollectionComponent",
    "attributes": {
        "loads": [
            {
                "pipeline": ".load.duckdb_repo_reactions_issues_only_pipeline",
                "source": ".load.duckdb_repo_reactions_issues_only_source",
            }
        ]
    },
}


def test_basic_component_load() -> None:
    with (
        environ({"SOURCES__ACCESS_TOKEN": "fake"}),
        setup_dlt_component(
            load_py_contents=github_load,
            component_body=BASIC_GITHUB_COMPONENT_BODY,
            setup_dlt_sources=lambda: dlt_init("github", "snowflake"),
        ) as (
            component,
            defs,
        ),
    ):
        loads = component.loads
        assert len(loads) == 1

        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey(["duckdb_issues", "issues"]),
            AssetKey(["github_reactions_issues"]),
        }


GITHUB_COMPONENT_BODY_WITH_ABSOLUTE_PATH = {
    "type": "dagster_dlt.DltLoadCollectionComponent",
    "attributes": {
        "loads": [
            {
                "pipeline": "foo_bar.defs.ingest.load.duckdb_repo_reactions_issues_only_pipeline",
                "source": "foo_bar.defs.ingest.load.duckdb_repo_reactions_issues_only_source",
            }
        ]
    },
}


def test_component_load_abs_path_load_py() -> None:
    with (
        environ({"SOURCES__ACCESS_TOKEN": "fake"}),
        setup_dlt_component(
            load_py_contents=github_load,
            component_body=GITHUB_COMPONENT_BODY_WITH_ABSOLUTE_PATH,
            setup_dlt_sources=lambda: dlt_init("github", "snowflake"),
        ) as (
            component,
            defs,
        ),
    ):
        loads = component.loads
        assert len(loads) == 1

        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey(["duckdb_issues", "issues"]),
            AssetKey(["github_reactions_issues"]),
        }


def github_load_multiple_pipelines():
    import dlt

    from .github import github_reactions, github_repo_events  # type: ignore

    duckdb_repo_reactions_issues_only_source = github_reactions(
        "duckdb", "duckdb", items_per_page=100, max_items=100
    ).with_resources("issues")
    duckdb_repo_reactions_issues_only_pipeline = dlt.pipeline(
        "github_reactions",
        destination="snowflake",
        dataset_name="duckdb_issues",
    )

    dagster_events_source = github_repo_events("dagster-io", "dagster", access_token="")
    dagster_events_pipeline = dlt.pipeline(
        "github_events", destination="snowflake", dataset_name="dagster_events"
    )


MULTIPLE_GITHUB_COMPONENT_BODY = {
    "type": "dagster_dlt.DltLoadCollectionComponent",
    "attributes": {
        "loads": [
            {
                "pipeline": ".load.duckdb_repo_reactions_issues_only_pipeline",
                "source": ".load.duckdb_repo_reactions_issues_only_source",
            },
            {
                "pipeline": ".load.dagster_events_pipeline",
                "source": ".load.dagster_events_source",
            },
        ]
    },
}


def test_component_load_multiple_pipelines() -> None:
    with (
        environ({"SOURCES__ACCESS_TOKEN": "fake"}),
        setup_dlt_component(
            load_py_contents=github_load_multiple_pipelines,
            component_body=MULTIPLE_GITHUB_COMPONENT_BODY,
            setup_dlt_sources=lambda: dlt_init("github", "snowflake"),
        ) as (
            component,
            defs,
        ),
    ):
        loads = component.loads
        assert len(loads) == 2

        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey(["duckdb_issues", "issues"]),
            AssetKey(["github_reactions_issues"]),
            AssetKey(["dagster_events", "repo_events"]),
            AssetKey(["github_repo_events_repo_events"]),
        }


def test_python_interface(dlt_pipeline: Pipeline):
    context = ComponentLoadContext.for_test()
    defs = DltLoadCollectionComponent(
        loads=[
            DltLoadSpecModel(
                pipeline=dlt_pipeline,
                source=dlt_source(),
            )
        ]
    ).build_defs(context)

    assert defs
    assert (defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey(["example", "repos"]),
        AssetKey(["example", "repo_issues"]),
        AssetKey(["pipeline_repos"]),
    }
