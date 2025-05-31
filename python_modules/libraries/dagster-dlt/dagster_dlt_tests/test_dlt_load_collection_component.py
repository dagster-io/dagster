# ruff: noqa: F841 TID252

import copy
import inspect
import subprocess
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

import pytest
from dagster import AssetKey, ComponentLoadContext
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd
from dagster._utils.env import environ
from dagster.components.testing import scaffold_defs_sandbox
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


@pytest.mark.parametrize(
    "attributes, assertion, should_error",
    [
        ({"group_name": "group"}, lambda asset_spec: asset_spec.group_name == "group", False),
        (
            {"owners": ["team:analytics"]},
            lambda asset_spec: asset_spec.owners == ["team:analytics"],
            False,
        ),
        ({"tags": {"foo": "bar"}}, lambda asset_spec: asset_spec.tags.get("foo") == "bar", False),
        (
            {"kinds": ["snowflake", "dbt"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds and "dbt" in asset_spec.kinds,
            False,
        ),
        (
            {"tags": {"foo": "bar"}, "kinds": ["snowflake", "dbt"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds
            and "dbt" in asset_spec.kinds
            and asset_spec.tags.get("foo") == "bar",
            False,
        ),
        ({"code_version": "1"}, lambda asset_spec: asset_spec.code_version == "1", False),
        (
            {"description": "some description"},
            lambda asset_spec: asset_spec.description == "some description",
            False,
        ),
        (
            {"metadata": {"foo": "bar"}},
            lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
            False,
        ),
        (
            {"deps": ["customers"]},
            lambda asset_spec: len(asset_spec.deps) == 1
            and asset_spec.deps[0].asset_key == AssetKey("customers"),
            False,
        ),
        (
            {"automation_condition": "{{ automation_condition.eager() }}"},
            lambda asset_spec: asset_spec.automation_condition is not None,
            False,
        ),
        (
            {"key": "{{ spec.key.to_user_string() + '_suffix' }}"},
            lambda asset_spec: asset_spec.key == AssetKey(["duckdb_issues", "issues_suffix"]),
            False,
        ),
        (
            {"key_prefix": "cool_prefix"},
            lambda asset_spec: asset_spec.key.has_prefix(["cool_prefix"]),
            False,
        ),
    ],
    ids=[
        "group_name",
        "owners",
        "tags",
        "kinds",
        "tags-and-kinds",
        "code-version",
        "description",
        "metadata",
        "deps",
        "automation_condition",
        "key",
        "key_prefix",
    ],
)
def test_translation(
    attributes: Mapping[str, Any],
    assertion: Optional[Callable[[AssetSpec], bool]],
    should_error: bool,
) -> None:
    wrapper = pytest.raises(Exception) if should_error else nullcontext()
    with wrapper:
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
            if "key" in attributes:
                key = AssetKey(["duckdb_issues", "issues_suffix"])
            elif "key_prefix" in attributes:
                key = AssetKey(["cool_prefix", "duckdb_issues", "issues"])
            else:
                key = AssetKey(["duckdb_issues", "issues"])

            assets_def = defs.resolve_assets_def(key)
            if assertion:
                assert assertion(assets_def.get_asset_spec(key))


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


# >>>>>>> 1dbdf22ea8 (Scaffolding infrastructure)


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
    ).build_defs(ComponentLoadContext.for_test())

    asset_def = cast("AssetsDefinition", next(iter(defs.assets or [])))
    result = materialize(
        assets=[asset_def], resources={"dlt_pipeline_resource": DagsterDltResource()}
    )
    assert result.success
