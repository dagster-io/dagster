# ruff: noqa: F841 TID252

import copy
import importlib
import inspect
import subprocess
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

import pytest
import yaml
from click.testing import CliRunner
from dagster import AssetKey
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path, pushd
from dagster._utils.env import environ
from dagster.components import ComponentLoadContext
from dagster.components.cli import cli
from dagster.components.core.context import use_component_load_context
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dlt import DagsterDltResource, DltLoadCollectionComponent
from dagster_dlt.components.dlt_load_collection.component import DltLoadSpecModel

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition


ensure_dagster_tests_import()
from dagster_tests.components_tests.utils import get_underlying_component
from dlt import Pipeline

from dagster_dlt_tests.dlt_test_sources.duckdb_with_transformer import pipeline as dlt_source

ensure_dagster_tests_import()
ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, isolated_example_project_foo_bar


def dlt_init(source: str, dest: str) -> None:
    yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
    subprocess.check_call(["dlt", "init", source, dest], stdin=yes.stdout)


@contextmanager
def setup_dlt_ready_project() -> Iterator[None]:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        alter_sys_path(to_add=[str(Path.cwd() / "src")], to_remove=[]),
    ):
        yield


@contextmanager
def setup_dlt_component(
    load_py_contents: Callable, component_body: dict[str, Any], setup_dlt_sources: Callable
) -> Iterator[tuple[DltLoadCollectionComponent, Definitions]]:
    """Sets up a components project with a dlt component based on provided params."""
    with setup_dlt_ready_project():
        defs_path = Path.cwd() / "src" / "foo_bar" / "defs"
        component_path = defs_path / "ingest"
        component_path.mkdir(parents=True, exist_ok=True)

        with pushd(str(component_path)):
            setup_dlt_sources()

        Path(component_path / "load.py").write_text(
            textwrap.dedent("\n".join(inspect.getsource(load_py_contents).split("\n")[1:]))
        )
        (component_path / "defs.yaml").write_text(yaml.safe_dump(component_body))

        defs_root = importlib.import_module("foo_bar.defs.ingest")
        project_root = Path.cwd()

        context = ComponentLoadContext.for_module(defs_root, project_root)
        with use_component_load_context(context):
            component = get_underlying_component(context)
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

            assets_def = defs.get_assets_def(key)
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
    assert (defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey(["example", "repos"]),
        AssetKey(["example", "repo_issues"]),
        AssetKey(["pipeline_repos"]),
    }


def test_scaffold_bare_component():
    runner = CliRunner()

    with setup_dlt_ready_project() as project_path:
        result = runner.invoke(
            cli,
            [
                "scaffold",
                "object",
                "dagster_dlt.DltLoadCollectionComponent",
                "src/foo_bar/defs/my_barebones_dlt_component",
                "--scaffold-format",
                "yaml",
            ],
        )
        assert result.exit_code == 0
        assert Path("src/foo_bar/defs/my_barebones_dlt_component/loads.py").exists()
        assert Path("src/foo_bar/defs/my_barebones_dlt_component/defs.yaml").exists()

        defs_root = importlib.import_module("foo_bar.defs.my_barebones_dlt_component")
        project_root = Path.cwd()

        context = ComponentLoadContext.for_module(defs_root, project_root)
        with use_component_load_context(context):
            component = get_underlying_component(context)
            assert isinstance(component, DltLoadCollectionComponent)
            defs = component.build_defs(context)

        assert len(component.loads) == 1
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey(["example", "hello_world"]),
            AssetKey(["my_source_hello_world"]),
        }


def test_scaffold_component_with_source_and_destination():
    runner = CliRunner()

    with setup_dlt_ready_project() as project_path, environ({"SOURCES__ACCESS_TOKEN": "fake"}):
        result = runner.invoke(
            cli,
            [
                "scaffold",
                "object",
                "dagster_dlt.DltLoadCollectionComponent",
                "src/foo_bar/defs/my_barebones_dlt_component",
                "--scaffold-format",
                "yaml",
                "--json-params",
                '{"source": "github", "destination": "snowflake"}',
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path("src/foo_bar/defs/my_barebones_dlt_component/loads.py").exists()
        assert Path("src/foo_bar/defs/my_barebones_dlt_component/defs.yaml").exists()

        defs_root = importlib.import_module("foo_bar.defs.my_barebones_dlt_component")
        project_root = Path.cwd()

        context = ComponentLoadContext.for_module(defs_root, project_root)
        with use_component_load_context(context):
            component = get_underlying_component(context)
            assert isinstance(component, DltLoadCollectionComponent)

        # should be many loads, not hardcoding in case dlt changes
        assert len(component.loads) > 1


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
