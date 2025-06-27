# ruff: noqa: F841 TID252

import copy
import inspect
import subprocess
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

import pytest
from dagster import AssetKey
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd
from dagster._utils.env import environ
from dagster.components.core.tree import ComponentTree
from dagster.components.testing import TestTranslationBatched, scaffold_defs_sandbox
from dagster_dlt import DagsterDltResource, DltLoadCollectionComponent
from dagster_dlt.components.dlt_load_collection.component import DltLoadSpecModel

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition


from dlt import Pipeline

from dagster_dlt_tests.dlt_test_sources.duckdb_with_transformer import pipeline as dlt_source


def dlt_init(source: str, dest: str) -> None:
    yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
    subprocess.check_call(["dlt", "init", source, dest], stdin=yes.stdout)


@contextmanager
def setup_dlt_component(
    load_py_contents: Callable,
    component_body: dict[str, Any],
    setup_dlt_sources: Callable,
    project_name: Optional[str] = None,
) -> Iterator[tuple[DltLoadCollectionComponent, Definitions]]:
    """Sets up a components project with a dlt component based on provided params."""
    with scaffold_defs_sandbox(
        component_cls=DltLoadCollectionComponent,
        scaffold_params={"source": "github", "destination": "snowflake"},
        component_path="ingest",
        project_name=project_name,
    ) as defs_sandbox:
        with pushd(str(defs_sandbox.defs_folder_path)):
            setup_dlt_sources()

        Path(defs_sandbox.defs_folder_path / "load.py").write_text(
            textwrap.dedent("\n".join(inspect.getsource(load_py_contents).split("\n")[1:]))
        )

        with defs_sandbox.load(component_body=component_body) as (component, defs):
            assert isinstance(component, DltLoadCollectionComponent)
            yield component, defs


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

        assert defs.resolve_asset_graph().get_all_asset_keys() == {
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
            project_name="foo_bar",
        ) as (
            component,
            defs,
        ),
    ):
        loads = component.loads
        assert len(loads) == 1

        assert defs.resolve_asset_graph().get_all_asset_keys() == {
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

        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["duckdb_issues", "issues"]),
            AssetKey(["github_reactions_issues"]),
            AssetKey(["dagster_events", "repo_events"]),
            AssetKey(["github_repo_events_repo_events"]),
        }


class TestDltTranslation(TestTranslationBatched):
    def test_translation(
        self,
        dlt_pipeline: Pipeline,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
    ) -> None:
        body = copy.deepcopy(BASIC_GITHUB_COMPONENT_BODY)
        body["attributes"]["loads"][0]["translation"] = attributes
        with (
            environ({"SOURCES__ACCESS_TOKEN": "fake"}),
            setup_dlt_component(
                load_py_contents=github_load,
                component_body=body,
                setup_dlt_sources=lambda: dlt_init("github", "snowflake"),
            ) as (
                component,
                defs,
            ),
        ):
            key = AssetKey(["duckdb_issues", "issues"])
            if key_modifier:
                key = key_modifier(key)

            assets_def = defs.resolve_assets_def(key)
            assert assertion(assets_def.get_asset_spec(key))


def test_python_interface(dlt_pipeline: Pipeline):
    context = ComponentTree.for_test().decl_load_context
    defs = DltLoadCollectionComponent(
        loads=[
            DltLoadSpecModel(
                pipeline=dlt_pipeline,
                source=dlt_source(),
            )
        ]
    ).build_defs(context)

    assert defs
    assert (defs.resolve_asset_graph().get_all_asset_keys()) == {
        AssetKey(["example", "repos"]),
        AssetKey(["example", "repo_issues"]),
        AssetKey(["pipeline_repos"]),
    }


def test_scaffold_bare_component() -> None:
    with scaffold_defs_sandbox(component_cls=DltLoadCollectionComponent) as defs_sandbox:
        assert defs_sandbox.defs_folder_path.exists()
        assert (defs_sandbox.defs_folder_path / "defs.yaml").exists()
        assert (defs_sandbox.defs_folder_path / "loads.py").exists()

        with defs_sandbox.load() as (component, defs):
            assert isinstance(component, DltLoadCollectionComponent)
            assert len(component.loads) == 1
            assert defs.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["example", "hello_world"]),
                AssetKey(["my_source_hello_world"]),
            }


@pytest.mark.parametrize(
    "source, destination",
    [
        ("github", "snowflake"),
        ("sql_database", "duckdb"),
    ],
)
def test_scaffold_component_with_source_and_destination(source: str, destination: str) -> None:
    with (
        scaffold_defs_sandbox(
            component_cls=DltLoadCollectionComponent,
            scaffold_params={"source": source, "destination": destination},
        ) as defs_sandbox,
        environ({"SOURCES__ACCESS_TOKEN": "fake"}),
    ):
        assert defs_sandbox.defs_folder_path.exists()
        assert (defs_sandbox.defs_folder_path / "defs.yaml").exists()
        assert (defs_sandbox.defs_folder_path / "loads.py").exists()

        with defs_sandbox.load() as (component, defs):
            assert isinstance(component, DltLoadCollectionComponent)
            # scaffolder generates a silly sample load right now because the complex parsing logic is flaky
            assert len(component.loads) == 1


def test_execute_component(dlt_pipeline: Pipeline):
    defs = DltLoadCollectionComponent(
        loads=[
            DltLoadSpecModel(
                source=dlt_source(),
                pipeline=dlt_pipeline,
            )
        ]
    ).build_defs(ComponentTree.for_test().decl_load_context)

    asset_def = cast("AssetsDefinition", next(iter(defs.assets or [])))
    result = materialize(
        assets=[asset_def], resources={"dlt_pipeline_resource": DagsterDltResource()}
    )
    assert result.success
