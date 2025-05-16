import inspect
import re
import shutil
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Union

import pytest
from dagster.components.utils import format_error_message
from dagster_dg.cli.list import MIN_DAGSTER_COMPONENTS_LIST_DEFINITIONS_OUTPUT_FILE_OPTION_VERSION
from dagster_dg.component import MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_shared.libraries import increment_micro_version
from packaging.version import Version

ensure_dagster_dg_tests_import()

from unittest import mock

from dagster_dg.utils import ensure_dagster_dg_tests_import

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    fixed_panel_width,
    isolated_components_venv,
    isolated_example_component_library_foo_bar,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    match_terminal_box_output,
    standardize_box_characters,
)


@pytest.fixture
def capture_stderr_from_components_cli_invocations():
    with mock.patch("dagster_dg.context._should_capture_components_cli_stderr", return_value=True):
        yield


# ########################
# ##### PROJECT
# ########################


def test_list_project_success():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke("scaffold", "project", "foo")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "project", "projects/bar")
        assert_runner_result(result)
        result = runner.invoke("scaffold", "project", "more_projects/baz")
        assert_runner_result(result)
        result = runner.invoke("list", "project")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
                foo
                projects/bar
                more_projects/baz
            """).strip()
        )


@pytest.mark.parametrize("alias", ["project", "projects"])
def test_list_projects_aliases(alias: str):
    with ProxyRunner.test() as runner:
        assert_runner_result(runner.invoke("list", alias, "--help"))


# ########################
# ##### COMPONENT
# ########################


def test_list_components_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=False),
    ):
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        result = runner.invoke("list", "component")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            qux
        """).strip()
        )


# ########################
# PLUGINS
# ########################

_EXPECTED_COMPONENT_TYPES = textwrap.dedent("""
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Plugin       ┃ Objects                                                                                               ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ dagster_test │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓ │
│              │ ┃ Symbol                                             ┃ Summary              ┃ Features              ┃ │
│              │ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩ │
│              │ │ dagster_test.components.AllMetadataEmptyComponent  │                      │ [component,           │ │
│              │ │                                                    │                      │ scaffold-target]      │ │
│              │ ├────────────────────────────────────────────────────┼──────────────────────┼───────────────────────┤ │
│              │ │ dagster_test.components.ComplexAssetComponent      │ An asset that has a  │ [component,           │ │
│              │ │                                                    │ complex schema.      │ scaffold-target]      │ │
│              │ ├────────────────────────────────────────────────────┼──────────────────────┼───────────────────────┤ │
│              │ │ dagster_test.components.SimpleAssetComponent       │ A simple asset that  │ [component,           │ │
│              │ │                                                    │ returns a constant   │ scaffold-target]      │ │
│              │ │                                                    │ string value.        │                       │ │
│              │ ├────────────────────────────────────────────────────┼──────────────────────┼───────────────────────┤ │
│              │ │ dagster_test.components.SimplePipesScriptComponent │ A simple asset that  │ [component,           │ │
│              │ │                                                    │ runs a Python script │ scaffold-target]      │ │
│              │ │                                                    │ with the Pipes       │                       │ │
│              │ │                                                    │ subprocess client.   │                       │ │
│              │ └────────────────────────────────────────────────────┴──────────────────────┴───────────────────────┘ │
└──────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────┘
""").strip()

_EXPECTED_COMPONENT_TYPES_JSON = textwrap.dedent("""
    [
        {
            "key": "dagster_test.components.AllMetadataEmptyComponent",
            "summary": null,
            "features": [
                "component",
                "scaffold-target"
            ]
        },
        {
            "key": "dagster_test.components.ComplexAssetComponent",
            "summary": "An asset that has a complex schema.",
            "features": [
                "component",
                "scaffold-target"
            ]
        },
        {
            "key": "dagster_test.components.SimpleAssetComponent",
            "summary": "A simple asset that returns a constant string value.",
            "features": [
                "component",
                "scaffold-target"
            ]
        },
        {
            "key": "dagster_test.components.SimplePipesScriptComponent",
            "summary": "A simple asset that runs a Python script with the Pipes subprocess client.",
            "features": [
                "component",
                "scaffold-target"
            ]
        }
    ]

""").strip()


def test_list_plugins_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        with fixed_panel_width(width=120):
            result = runner.invoke("list", "plugins")
            assert_runner_result(result)
            # strip the first two lines of logging output
            output = "\n".join(result.output.split("\n")[2:])
            match_terminal_box_output(output.strip(), _EXPECTED_COMPONENT_TYPES)


def test_list_plugins_json_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("list", "plugins", "--json")
        assert_runner_result(result)
        # strip the first line of logging output
        output = "\n".join(result.output.split("\n")[2:])
        assert output.strip() == _EXPECTED_COMPONENT_TYPES_JSON


def test_list_plugins_backcompat():
    version = increment_micro_version(MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION, -1)
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            dagster_version=version,
            use_editable_dagster=False,
            python_environment="uv_managed",
        ),
    ):
        result = runner.invoke("list", "plugins", "--json")
        assert_runner_result(result)

        # We don't care about the precise output from the old version, only that we can successfully
        # call it and successfully get some plugin objects returned.
        assert "dagster.asset" in result.output


def test_list_plugins_includes_modules_with_no_objects():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("list", "plugins", "--name-only")
        assert_runner_result(result)
        assert "foo_bar" in result.output


def test_list_plugins_bad_entry_point_fails():
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        # Delete the components package referenced by the entry point
        shutil.rmtree("src/foo_bar/components")

        # Disable cache to force re-discovery of deleted entry point
        result = runner.invoke("list", "plugins", "--disable-cache")
        assert_runner_result(result, exit_0=False)

        output = standardize_box_characters(result.output)

        expected_header_message = format_error_message("""
            Error loading entry point `foo_bar.components` in group `dagster_dg.plugin`.
        """)
        assert expected_header_message in output

        # Hard to test for the exact entire Panel output here, but make sure the title line is there.
        panel_title_pattern = standardize_box_characters(
            textwrap.dedent(r"""
            ╭─+ Entry point error \(foo_bar.components\)
        """).strip()
        )

        assert re.search(panel_title_pattern, output)


@pytest.mark.parametrize("alias", ["plugin", "plugins"])
def test_list_plugins_aliases(alias: str):
    with ProxyRunner.test() as runner:
        assert_runner_result(runner.invoke("list", alias, "--help"))


# ########################
# ##### DEFS
# ########################

_EXPECTED_DEFS = textwrap.dedent("""
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Section   ┃ Definitions                                           ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Assets    │ ┏━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓ │
│           │ ┃ Key        ┃ Group   ┃ Deps ┃ Kinds ┃ Description ┃ │
│           │ ┡━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩ │
│           │ │ my_asset_1 │ default │      │       │             │ │
│           │ ├────────────┼─────────┼──────┼───────┼─────────────┤ │
│           │ │ my_asset_2 │ default │      │       │             │ │
│           │ └────────────┴─────────┴──────┴───────┴─────────────┘ │
│ Jobs      │ ┏━━━━━━━━┓                                            │
│           │ ┃ Name   ┃                                            │
│           │ ┡━━━━━━━━┩                                            │
│           │ │ my_job │                                            │
│           │ └────────┘                                            │
│ Schedules │ ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                       │
│           │ ┃ Name        ┃ Cron schedule ┃                       │
│           │ ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                       │
│           │ │ my_schedule │ @daily        │                       │
│           │ └─────────────┴───────────────┘                       │
│ Sensors   │ ┏━━━━━━━━━━━┓                                         │
│           │ ┃ Name      ┃                                         │
│           │ ┡━━━━━━━━━━━┩                                         │
│           │ │ my_sensor │                                         │
│           │ └───────────┘                                         │
└───────────┴───────────────────────────────────────────────────────┘
""").strip()

_EXPECTED_DEFS_JSON = textwrap.dedent("""
    [
        {
            "key": "my_asset_1",
            "deps": [],
            "kinds": [],
            "group": "default",
            "description": null,
            "automation_condition": null
        },
        {
            "key": "my_asset_2",
            "deps": [],
            "kinds": [],
            "group": "default",
            "description": null,
            "automation_condition": null
        },
        {
            "name": "my_job"
        },
        {
            "name": "my_schedule",
            "cron_schedule": "@daily"
        },
        {
            "name": "my_sensor"
        }
    ]
""").strip()


@pytest.mark.parametrize("use_json", [True, False])
@pytest.mark.parametrize(
    "dagster_version",
    [
        "editable",  # most recent
        increment_micro_version(
            MIN_DAGSTER_COMPONENTS_LIST_DEFINITIONS_OUTPUT_FILE_OPTION_VERSION, -1
        ),
    ],
    ids=str,
)
def test_list_defs_succeeds(use_json: bool, dagster_version: Union[str, Version]):
    project_kwargs: dict[str, Any] = (
        {"use_editable_dagster": True}
        if dagster_version == "editable"
        else {
            "use_editable_dagster": False,
            "dagster_version": dagster_version,
        }
    )
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            python_environment="uv_managed",
            **project_kwargs,
        ),
    ):
        result = runner.invoke("scaffold", "dagster.components.DefsFolderComponent", "mydefs")
        assert_runner_result(result)

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
            f.write(defs_source)

        if use_json:
            result = runner.invoke("list", "defs", "--json")
            assert_runner_result(result)
            output = "\n".join(result.output.split("\n")[1:])
            assert output.strip() == _EXPECTED_DEFS_JSON
        else:
            result = runner.invoke("list", "defs")
            assert_runner_result(result)
            output = "\n".join(result.output.split("\n")[1:])
            match_terminal_box_output(output.strip(), _EXPECTED_DEFS)


def _sample_defs():
    from dagster import asset, job, schedule, sensor

    print("This will break JSON parsing if written to same stream as defs")  # noqa: T201

    @asset
    def my_asset_1(): ...

    @asset
    def my_asset_2(): ...

    @schedule(cron_schedule="@daily", target=[my_asset_1])
    def my_schedule(): ...

    @sensor(target=[my_asset_2])
    def my_sensor(): ...

    @job
    def my_job(): ...


_EXPECTED_COMPLEX_ASSET_DEFS = textwrap.dedent("""
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Section      ┃ Definitions                                                                      ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Assets       │ ┏━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┓                         │
│              │ ┃ Key     ┃ Group   ┃ Deps  ┃ Kinds ┃ Description      ┃                         │
│              │ ┡━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━┩                         │
│              │ │ alpha   │ group_1 │       │ sling │                  │                         │
│              │ ├─────────┼─────────┼───────┼───────┼──────────────────┤                         │
│              │ │ beta    │ group_2 │       │ dbt   │ This is beta.    │                         │
│              │ ├─────────┼─────────┼───────┼───────┼──────────────────┤                         │
│              │ │ delta   │ group_2 │ alpha │ dbt   │                  │                         │
│              │ │         │         │ beta  │       │                  │                         │
│              │ ├─────────┼─────────┼───────┼───────┼──────────────────┤                         │
│              │ │ epsilon │ group_2 │ delta │ dbt   │ This is epsilon. │                         │
│              │ └─────────┴─────────┴───────┴───────┴──────────────────┘                         │
│ Asset Checks │ ┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│              │ ┃ Key                    ┃ Additional Deps ┃ Description                       ┃ │
│              │ ┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│              │ │ alpha:alpha_beta_check │ alpha           │ This check is for alpha and beta. │ │
│              │ │                        │ beta            │                                   │ │
│              │ ├────────────────────────┼─────────────────┼───────────────────────────────────┤ │
│              │ │ alpha:alpha_check      │ alpha           │ This check is for alpha.          │ │
│              │ └────────────────────────┴─────────────────┴───────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────────────────────────────────────────┘
""").strip()


def test_list_defs_complex_assets_succeeds():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, python_environment="uv_managed"
        ),
    ):
        result = runner.invoke("scaffold", "dagster.components.DefsFolderComponent", "mydefs")
        assert_runner_result(result)

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        assert "No definitions are defined" in result.output
        assert "Definitions" not in result.output  # no table header means no table

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(
                inspect.getsource(_sample_complex_asset_defs).split("\n", 1)[1]
            )
            f.write(defs_source)

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = "\n".join(result.output.split("\n")[1:])
        match_terminal_box_output(output.strip(), _EXPECTED_COMPLEX_ASSET_DEFS)


def _sample_complex_asset_defs():
    import dagster as dg

    @dg.asset(kinds={"sling"}, group_name="group_1")
    def alpha():
        pass

    @dg.asset(
        kinds={"dbt"},
        group_name="group_2",
        description="This is beta.",
    )
    def beta():
        pass

    @dg.asset(
        kinds={"dbt"},
        group_name="group_2",
    )
    def delta(alpha, beta):
        pass

    @dg.asset(kinds={"dbt"}, group_name="group_2", description="This is epsilon.")
    def epsilon(delta):
        pass

    @dg.asset_check(asset=alpha)
    def alpha_check() -> dg.AssetCheckResult:
        """This check is for alpha."""
        return dg.AssetCheckResult(passed=True)

    @dg.asset_check(asset=alpha, additional_deps=[beta])
    def alpha_beta_check() -> dg.AssetCheckResult:
        """This check is for alpha and beta."""
        return dg.AssetCheckResult(passed=True)


_EXPECTED_ENV_VAR_ASSET_DEFS = textwrap.dedent("""
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Section ┃ Definitions                                    ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Assets  │ ┏━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓ │
│         │ ┃ Key   ┃ Group ┃ Deps ┃ Kinds ┃ Description ┃ │
│         │ ┡━━━━━━━╇━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩ │
│         │ │ alpha │ bar   │      │ sling │             │ │
│         │ └───────┴───────┴──────┴───────┴─────────────┘ │
└─────────┴────────────────────────────────────────────────┘
""").strip()


def test_list_defs_with_env_file_succeeds():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, python_environment="uv_managed"
        ),
    ):
        result = runner.invoke(
            "scaffold",
            "dagster.components.DefsFolderComponent",
            "mydefs",
        )
        assert_runner_result(result)

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(
                inspect.getsource(_sample_env_var_assets).split("\n", 1)[1]
            )
            f.write(defs_source)
            env_file_contents = textwrap.dedent("""
                GROUP_NAME=bar
            """)

        with Path(".env").open("w") as f:
            f.write(env_file_contents)

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = "\n".join(result.output.split("\n")[1:])
        match_terminal_box_output(output.strip(), _EXPECTED_ENV_VAR_ASSET_DEFS)


def _sample_env_var_assets():
    import os

    from dagster import asset

    @asset(kinds={"sling"}, group_name=os.getenv("GROUP_NAME", "MISSING"))
    def alpha():
        pass


@pytest.mark.parametrize("alias", ["def", "defs"])
def test_list_defs_aliases(alias: str):
    with ProxyRunner.test() as runner:
        assert_runner_result(runner.invoke("list", alias, "--help"))


def test_list_defs_fails_compact(capture_stderr_from_components_cli_invocations):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, python_environment="uv_managed"
        ),
    ):
        result = runner.invoke("scaffold", "dagster.components.DefsFolderComponent", "mydefs")
        assert_runner_result(result)

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_failed_defs).split("\n", 1)[1])
            f.write(defs_source)
        result = runner.invoke("list", "defs")
        assert_runner_result(result, exit_0=False)
        assert (
            "dagster system frames hidden, run dg check defs --verbose to see the full stack trace"
            in result.output
        )


def _sample_failed_defs():
    from dagster import asset

    @asset(required_resource_keys={"my_resource"})
    def my_asset_1(): ...


# ########################
# ##### ENV
# ########################


def test_list_env_succeeds(monkeypatch):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=False),
        tempfile.TemporaryDirectory() as cloud_config_dir,
    ):
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))
        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            No environment variables are defined for this project.
        """).strip()
        )

        Path(".env").write_text("FOO=bar")
        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
               ┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
               ┃ Env Var ┃ Value ┃ Components ┃
               ┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
               │ FOO     │ ✓     │            │
               └─────────┴───────┴────────────┘
        """).strip()
        )

        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "subfolder/mydefs"
        )
        assert_runner_result(result)
        Path("src/foo_bar/defs/subfolder/mydefs/defs.yaml").write_text(
            textwrap.dedent("""
                type: dagster_test.components.AllMetadataEmptyComponent

                requirements:
                    env:
                        - FOO
            """)
        )

        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
               ┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
               ┃ Env Var ┃ Value ┃ Components       ┃
               ┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
               │ FOO     │ ✓     │ subfolder/mydefs │
               └─────────┴───────┴──────────────────┘
        """).strip()
        )


@pytest.mark.parametrize("alias", ["env", "envs"])
def test_list_envs_aliases(alias: str):
    with ProxyRunner.test() as runner:
        assert_runner_result(runner.invoke("list", alias, "--help"))
