import importlib
import inspect
import json
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

import pytest
from dagster.components.utils import format_error_message
from dagster_dg_core.utils import activate_venv, ensure_dagster_dg_tests_import, set_toml_node

ensure_dagster_dg_tests_import()

from unittest import mock

from dagster_dg_core.utils import ensure_dagster_dg_tests_import
from dagster_dg_core_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    fixed_panel_width,
    isolated_components_venv,
    isolated_example_component_library_foo_bar,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    match_json_output,
    match_terminal_box_output,
    modify_dg_toml_config_as_dict,
    standardize_box_characters,
)


@pytest.fixture
def capture_stderr_from_components_cli_invocations():
    with mock.patch(
        "dagster_dg_core.context._should_capture_components_cli_stderr", return_value=True
    ):
        yield


# ########################
# ##### PROJECT
# ########################


def test_list_project_success():
    with ProxyRunner.test() as runner, isolated_example_workspace(runner):
        result = runner.invoke_create_dagster("project", "foo")
        assert_runner_result(result)
        result = runner.invoke_create_dagster("project", "projects/bar")
        assert_runner_result(result)
        result = runner.invoke_create_dagster("project", "more_projects/baz")
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
# ##### COMPONENTS
# ########################

_EXPECTED_COMPONENT_TYPES_TABLE = textwrap.dedent("""
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Key                                                ┃ Summary                                                         ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ dagster_test.components.AllMetadataEmptyComponent  │ Summary.                                                        │
    ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ dagster_test.components.ComplexAssetComponent      │ An asset that has a complex schema.                             │
    ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ dagster_test.components.SimpleAssetComponent       │ A simple asset that returns a constant string value.            │
    ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────┤
    │ dagster_test.components.SimplePipesScriptComponent │ A simple asset that runs a Python script with the Pipes         │
    │                                                    │ subprocess client.                                              │
    └────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┘
""").strip()

_EXPECTED_COMPONENTS_JSON = textwrap.dedent("""
    [
        {
            "key": "dagster_test.components.AllMetadataEmptyComponent",
            "summary": "Summary."
        },
        {
            "key": "dagster_test.components.ComplexAssetComponent",
            "summary": "An asset that has a complex schema."
        },
        {
            "key": "dagster_test.components.SimpleAssetComponent",
            "summary": "A simple asset that returns a constant string value."
        },
        {
            "key": "dagster_test.components.SimplePipesScriptComponent",
            "summary": "A simple asset that runs a Python script with the Pipes subprocess client."
        }
    ]
""").strip()


def test_list_components_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        with fixed_panel_width(width=120):
            result = runner.invoke("list", "components")
            assert_runner_result(result)
            match_terminal_box_output(result.output.strip(), _EXPECTED_COMPONENT_TYPES_TABLE)


def test_list_components_json_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        assert match_json_output(result.output.strip(), _EXPECTED_COMPONENTS_JSON)


def test_list_components_filtered():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("list", "components", "--json", "--package", "fake")
        assert_runner_result(result)
        assert result.output.strip() == "[]"

        for module in ["dagster_test", "dagster_test.components"]:
            result = runner.invoke("list", "components", "--json", "--package", module)
            assert_runner_result(result)
            assert match_json_output(result.output.strip(), _EXPECTED_COMPONENTS_JSON)


def test_list_components_project_wildcard_pattern():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold", "component", "foo_bar.components.my_component.MyComponent"
        )
        importlib.invalidate_caches()  # Needed to make sure new submodule is discoverable
        assert_runner_result(result)

        # Remove the generated registry module entry, confirm that our scaffolded component is not
        # listed
        with modify_dg_toml_config_as_dict(Path("pyproject.toml")) as config:
            set_toml_node(config, ("project", "registry_modules"), [])
        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        components = [entry["key"] for entry in json.loads(result.output.strip())]
        assert "foo_bar.components.my_component.MyComponent" not in components

        # Add a wildcard matching our scaffolded component, confirm that it is listed
        with modify_dg_toml_config_as_dict(Path("pyproject.toml")) as config:
            set_toml_node(config, ("project", "registry_modules"), ["foo_bar.components.*"])
        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        components = [entry["key"] for entry in json.loads(result.output.strip())]

        assert "foo_bar.components.my_component.MyComponent" in components


def test_list_components_project_wildcard_pattern_no_duplicates():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold", "component", "foo_bar.components.my_component.MyComponent"
        )
        importlib.invalidate_caches()  # Needed to make sure new submodule is discoverable
        assert_runner_result(result)

        # Add a wildcard that will match a component already in the list
        with modify_dg_toml_config_as_dict(Path("pyproject.toml")) as config:
            existing_value = config["project"]["registry_modules"]
            set_toml_node(
                config, ("project", "registry_modules"), [*existing_value, "foo_bar.components.*"]
            )
        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        components = [entry["key"] for entry in json.loads(result.output.strip())]
        assert (
            len([c for c in components if c == "foo_bar.components.my_component.MyComponent"]) == 1
        )


def test_list_components_bad_entry_point_fails():
    _assert_entry_point_error(["list", "components"])


@pytest.mark.parametrize("alias", ["component", "components"])
def test_list_component_aliases(alias: str):
    with ProxyRunner.test() as runner:
        assert_runner_result(runner.invoke("list", alias, "--help"))


# ########################
# PLUGIN MODULES
# ########################

_EXPECTED_PLUGINS_TABLE = textwrap.dedent("""
┏━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Module                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ dagster_test.components │
└─────────────────────────┘
""").strip()

_EXPECTED_PLUGIN_JSON = textwrap.dedent("""
    [
        {
            "module": "dagster_test.components"
        }
    ]
""").strip()


def test_list_registry_modules_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        with fixed_panel_width(width=120):
            result = runner.invoke("list", "registry-modules")
            assert_runner_result(result)

            match_terminal_box_output(result.output.strip(), _EXPECTED_PLUGINS_TABLE)


def test_list_registry_modules_json_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke("list", "registry-modules", "--json")
        assert_runner_result(result)

        assert match_json_output(result.output.strip(), _EXPECTED_PLUGIN_JSON)


def test_list_registry_modules_includes_modules_with_no_objects():
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        result = runner.invoke("list", "registry-modules")
        assert_runner_result(result)
        assert "foo_bar" in result.output


def test_list_registry_modules_bad_entry_point_fails():
    _assert_entry_point_error(["list", "registry-modules"])


@pytest.mark.parametrize("alias", ["registry-module", "registry-modules"])
def test_list_registry_modules_aliases(alias: str):
    with ProxyRunner.test() as runner:
        assert_runner_result(runner.invoke("list", alias, "--help"))


# ########################
# ##### COMPONENT TREE
# ########################


def test_list_component_tree_succeeds(snapshot):
    project_kwargs: dict[str, Any] = {"use_editable_dagster": True}
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            **project_kwargs,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            result = subprocess.run(
                ["dg", "scaffold", "defs", "dagster.FunctionComponent", "my_function"],
                check=True,
            )

            # touch plain python file
            Path("src/foo_bar/defs/assets").mkdir(parents=True, exist_ok=True)
            Path("src/foo_bar/defs/assets/asset.py").touch()

            Path("src/foo_bar/defs/pythonic_components").mkdir(parents=True, exist_ok=True)
            Path("src/foo_bar/defs/pythonic_components/my_component.py").write_text(
                textwrap.dedent(
                    """
                    import dagster as dg

                    class PyComponent(dg.Component, dg.Model, dg.Resolvable):
                        asset: dg.ResolvedAssetSpec

                        def build_defs(self, context):
                            return dg.Definitions(assets=[self.asset])

                    @dg.component_instance
                    def first(_):
                        return PyComponent(asset=dg.AssetSpec("first_py"))

                    @dg.component_instance
                    def second(_) -> PyComponent:
                        return PyComponent(asset=dg.AssetSpec("second_py"))
                    """
                )
            )

            result = subprocess.run(
                ["dg", "list", "component-tree"], check=True, capture_output=True
            )
            snapshot.assert_match(result.stdout.decode("utf-8").strip())


# ########################
# ##### DEFS
# ########################


@pytest.mark.parametrize("use_json", [True, False])
def test_list_defs_succeeds(use_json: bool, snapshot):
    project_kwargs: dict[str, Any] = {"use_editable_dagster": True}
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            **project_kwargs,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            result = subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
                f.write(defs_source)

            if use_json:
                result = subprocess.run(
                    ["dg", "list", "defs", "--json"], capture_output=True, check=True
                )
                snapshot.assert_match(result.stdout.decode("utf-8").strip())
            else:
                result = subprocess.run(["dg", "list", "defs"], check=True, capture_output=True)
                snapshot.assert_match(result.stdout.decode("utf-8").strip())


def _asset_1():
    from dagster import asset

    @asset
    def my_asset_1():
        pass


def _asset_2():
    from dagster import asset

    @asset
    def my_asset_2():
        pass


def _asset_3():
    from dagster import asset

    @asset
    def my_asset_3():
        pass


@pytest.mark.parametrize(
    "path,should_error,expected_assets,not_expected_assets",
    [
        ("src/foo_bar/defs", False, ["my_asset_1", "my_asset_2", "my_asset_3"], []),
        ("src/foo_bar/defs/asset1.py", False, ["my_asset_1"], ["my_asset_2", "my_asset_3"]),
        (
            "src/foo_bar/defs/subfolder/asset2.py",
            False,
            ["my_asset_2"],
            ["my_asset_1", "my_asset_3"],
        ),
        ("src/foo_bar/defs/subfolder", False, ["my_asset_2", "my_asset_3"], ["my_asset_1"]),
        ("src/foo_bar/defs/does_not_exist.py", True, [], []),
    ],
)
def test_list_defs_with_path(
    path: str, should_error: bool, expected_assets: list[str], not_expected_assets: list[str]
):
    project_kwargs: dict[str, Any] = {"use_editable_dagster": True}
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
            **project_kwargs,
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        Path("src/foo_bar/defs/subfolder").mkdir(parents=True, exist_ok=True)

        defs_source = textwrap.dedent(inspect.getsource(_asset_1).split("\n", 1)[1])
        Path("src/foo_bar/defs/asset1.py").write_text(defs_source)

        defs_source = textwrap.dedent(inspect.getsource(_asset_2).split("\n", 1)[1])
        Path("src/foo_bar/defs/subfolder/asset2.py").write_text(defs_source)

        defs_source = textwrap.dedent(inspect.getsource(_asset_3).split("\n", 1)[1])
        Path("src/foo_bar/defs/subfolder/asset3.py").write_text(defs_source)

        result = subprocess.run(
            ["dg", "list", "defs", "--path", path], check=False, capture_output=True
        )
        if should_error:
            assert result.returncode != 0
        else:
            assert result.returncode == 0, result.stderr.decode("utf-8")
            output = result.stdout.decode("utf-8").strip()

            for asset in expected_assets:
                assert asset in output
            for asset in not_expected_assets:
                assert asset not in output


def _sample_defs():
    from dagster import ConfigurableResource, Definitions, asset, job, schedule, sensor

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

    class MyResource(ConfigurableResource):
        my_int: int

    defs = Definitions(  # noqa:F841
        assets=[my_asset_1, my_asset_2],
        jobs=[my_job],
        schedules=[my_schedule],
        sensors=[my_sensor],
        resources={"my_resource": MyResource(my_int=1)},
    )


def test_list_defs_complex_assets_succeeds(snapshot):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=True) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            result = subprocess.run(["dg", "list", "defs"], check=True, capture_output=True)
            assert "No definitions are defined" in result.stdout.decode("utf-8")
            assert "Definitions" not in result.stdout.decode(
                "utf-8"
            )  # no table header means no table

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(
                    inspect.getsource(_sample_complex_asset_defs).split("\n", 1)[1]
                )
                f.write(defs_source)

            result = subprocess.run(["dg", "list", "defs"], check=True, capture_output=True)
            snapshot.assert_match(result.stdout.decode("utf-8").strip())


def test_list_defs_column_selection():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=True) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(
                    inspect.getsource(_sample_complex_asset_defs).split("\n", 1)[1]
                )
                f.write(defs_source)

            result = subprocess.run(
                ["dg", "list", "defs", "-c", "key"], check=True, capture_output=True
            )
            output = result.stdout.decode("utf-8")
            assert "alpha" in output
            assert "alpha:alpha_beta_check" in output
            assert "dbt" not in output
            assert "This is beta." not in output

            result = subprocess.run(
                ["dg", "list", "defs", "-c", "key", "-c", "description"],
                check=True,
                capture_output=True,
            )
            output = result.stdout.decode("utf-8")
            assert "alpha" in output
            assert "alpha:alpha_beta_check" in output
            assert "dbt" not in output
            assert "This is beta." in output

            # Ensure key/name is always included
            result = subprocess.run(
                ["dg", "list", "defs", "-c", "kinds"], check=True, capture_output=True
            )
            output = result.stdout.decode("utf-8")
            assert "alpha" in output
            assert "alpha:alpha_beta_check" in output
            assert "dbt" in output
            assert "This is beta." not in output


def test_list_defs_asset_subselection():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=True) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            result = subprocess.run(["dg", "list", "defs"], check=True, capture_output=True)
            assert "No definitions are defined" in result.stdout.decode("utf-8")
            assert "Definitions" not in result.stdout.decode(
                "utf-8"
            )  # no table header means no table

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(
                    inspect.getsource(_sample_complex_asset_defs).split("\n", 1)[1]
                )
                f.write(defs_source)

            result = subprocess.run(
                ["dg", "list", "defs", "--assets", "group:group_1"], check=True, capture_output=True
            )
            assert result.returncode == 0
            output = result.stdout.decode("utf-8")
            assert "sling" in output  # proxy for alpha asset in selection
            assert "This is beta." not in output  # proxy for beta asset in selection
            assert "delta" not in output
            assert "epsilon" not in output
            assert "alpha:alpha_check" in output
            assert "alpha:alpha_beta_check" in output
            result = subprocess.run(
                ["dg", "list", "defs", "--assets", "group:group_2"], check=True, capture_output=True
            )
            assert result.returncode == 0
            output = result.stdout.decode("utf-8")
            assert "sling" not in output  # proxy for alpha asset in selection
            assert "This is beta." in output  # proxy for beta asset in selection
            assert "delta" in output
            assert "epsilon" in output
            assert "alpha:alpha_check" not in output, output
            assert "alpha:alpha_beta_check" not in output


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

    @dg.asset(deps=[alpha, beta, delta, epsilon])
    def omega():
        """This is omega asset and it has a very very very long description that should be truncated.

        Wow look at all this amazing context that should very much not all show up in the output because
        it's far too long. This really should be truncated because there's no way anyone wants to read
        this much output in tabular form, it's simply too much.

        Args:
            fake_arg (Optional[str]): A fake argument wow very unimportant.
            fake_arg_2 (Optional[str]): A fake argument wow very unimportant as well.

        Raises:
            ValueError: If the fake argument is not None.
        """
        pass

    @dg.asset_check(asset=alpha)
    def alpha_check() -> dg.AssetCheckResult:
        """This check is for alpha."""
        return dg.AssetCheckResult(passed=True)

    @dg.asset_check(asset=alpha, additional_deps=[beta])
    def alpha_beta_check() -> dg.AssetCheckResult:
        """This check is for alpha and beta."""
        return dg.AssetCheckResult(passed=True)


def test_list_defs_with_env_file_succeeds(snapshot):
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=True) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

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

            result = subprocess.run(["dg", "list", "defs"], check=True, capture_output=True)
            snapshot.assert_match(result.stdout.decode("utf-8").strip())


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
            runner,
            in_workspace=False,
            use_editable_dagster=True,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(
                    inspect.getsource(_sample_failed_defs).split("\n", 1)[1]
                )
                f.write(defs_source)

            result = subprocess.run(["dg", "list", "defs"], check=False, capture_output=True)

            assert result.returncode != 0
            assert (
                "dagster system frames hidden, run dg check defs --verbose to see the full stack trace"
                in result.stderr.decode("utf-8")
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
            "scaffold",
            "defs",
            "dagster_test.components.AllMetadataEmptyComponent",
            "subfolder/mydefs",
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


def test_list_env_succeeds_with_no_defs(monkeypatch):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False, uv_sync=False),
        tempfile.TemporaryDirectory() as cloud_config_dir,
    ):
        shutil.rmtree(Path("src") / "foo_bar" / "defs")

        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

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


# ########################
# ##### HELPERS
# ########################


def _assert_entry_point_error(cmd: list[str]):
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        # Delete the components package referenced by the entry point
        shutil.rmtree("src/foo_bar/components")

        result = subprocess.run(
            ["dg", *cmd],
            check=False,
            capture_output=True,
        )
        assert result.returncode != 0

        output = standardize_box_characters(result.stdout.decode("utf-8"))

        expected_header_message = format_error_message("""
            Error loading entry point `foo_bar.components` in group `dagster_dg_cli.registry_modules`.
        """)
        assert expected_header_message in output

        # Hard to test for the exact entire Panel output here, but make sure the title line is there.
        panel_title_pattern = standardize_box_characters(
            textwrap.dedent(r"""
            ╭─+ Entry point error \(foo_bar.components\)
        """).strip()
        )

        assert re.search(panel_title_pattern, output)
