import importlib
import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest
from dagster_dg_core.utils import (
    activate_venv,
    create_toml_node,
    cross_platfrom_string_path,
    ensure_dagster_dg_tests_import,
    modify_toml_as_dict,
)

ensure_dagster_dg_tests_import()

from dagster_dg_core.utils import ensure_dagster_dg_tests_import
from dagster_dg_core_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_component_library_foo_bar,
    isolated_example_project_foo_bar,
    standardize_box_characters,
)

# ########################
# ##### DEFS
# ########################


def test_scaffold_defs_dynamic_subcommand_generation() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", "--help")
        assert_runner_result(result)

        normalized_output = standardize_box_characters(result.output)
        # These are wrapped in a table so it's hard to check exact output.
        for line in [
            "╭─ Commands",
            "│ dagster_test.components.AllMetadataEmptyComponent",
            "│ dagster_test.components.ComplexAssetComponent",
            "│ dagster_test.components.SimpleAssetComponent",
            "│ dagster_test.components.SimplePipesScriptComponent",
        ]:
            assert standardize_box_characters(line) in normalized_output


@pytest.mark.parametrize(
    "component_arg",
    ["dagster_test.components.AllMetadataEmptyComponent", "AllMetadataEmptyComponent"],
    ids=["full_key", "class_name"],
)
def test_scaffold_defs_classname_alias(component_arg: str) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", component_arg, "qux")
        assert_runner_result(result)


def test_scaffold_defs_classname_conflict_no_alias() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, uv_sync=True) as project_dir,
    ):
        # Need to use subprocess here because of cached in-process state
        with activate_venv(project_dir / ".venv"):
            subprocess.run(["dg", "scaffold", "component", "DefsFolderComponent"], check=True)
            assert Path("src/foo_bar/components/defs_folder_component.py").exists()
            # conflicts with the one from dagster, so we must provide input
            result = subprocess.check_output(
                ["dg", "scaffold", "defs", "DefsFolderComponent", "qux"], input="2\n", text=True
            )
            assert "Did you mean one of these" in result
            assert Path("src/foo_bar/defs/qux").exists()
            defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
            assert defs_yaml_path.exists()
            full_type = "foo_bar.components.defs_folder_component.DefsFolderComponent"
            assert f"type: {full_type}" in defs_yaml_path.read_text()


def test_scaffold_defs_validation_failure() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.SimplePipesScriptComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            Error validating scaffold parameters for `dagster_test.components.SimplePipesScriptComponent`:

            [
                {
                    "type": "missing",
                    "loc": [
                        "asset_key"
                    ],
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.11/v/missing"
                },
                {
                    "type": "missing",
                    "loc": [
                        "filename"
                    ],
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.11/v/missing"
                }
            ]
        """).strip()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_defs_component_no_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace, uv_sync=True),
    ):
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
        assert defs_yaml_path.exists()
        assert (
            "type: dagster_test.components.AllMetadataEmptyComponent" in defs_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_python_defs(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace, uv_sync=True) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster_test.components.AllMetadataEmptyComponent",
            "qux",
            "--format",
            "python",
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        component_py_path = Path("src/foo_bar/defs/qux/component.py")
        assert component_py_path.exists()

        component_py_path.write_text(
            component_py_path.read_text().replace("...", "return AllMetadataEmptyComponent()")
        )

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        assert "hardcoded_asset" in result.output


@pytest.mark.parametrize(
    "selection",
    ["", "y", "n", "a"],
    ids=["default", "explicit_yes", "quit", "invalid"],
)
def test_scaffold_defs_component_substring_single_match_success(selection: str) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, uv_sync=True),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "SimpleAsset",
            "qux",
            input=f"{selection}\n",
        )
        if selection in ["", "y"]:
            assert_runner_result(result)
            assert Path("src/foo_bar/defs/qux").exists()
            defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
            assert defs_yaml_path.exists()
            full_type = "dagster_test.components.SimpleAssetComponent"
            assert f"type: {full_type}" in defs_yaml_path.read_text()
        elif selection in ["a"]:
            assert_runner_result(result, exit_0=False)
            assert "Did you mean this one?" in result.output
            assert "Invalid selection" in result.output
        elif selection == "n":
            assert_runner_result(result)
            assert "Did you mean this one?" in result.output
            assert "Exiting." in result.output


def test_scaffold_defs_component_unregistered_success() -> None:
    """Ensure that a valid python symbol reference to a component type still works even if it is not registered."""
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("scaffold", "component", "Baz")
        assert_runner_result(result, exit_0=True)
        importlib.invalidate_caches()  # Ensure component discovery not blocked by python import cache

        # Remove registry module entry that would make the newly scaffolded component discoverable
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "registry_modules"), [])

        # Make sure the new component is not registered
        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        component_keys = [c["key"] for c in json.loads(result.stdout)]
        assert "foo_bar.components.baz.Baz" not in component_keys

        # dg scaffold defs foo_bar.components.baz.Baz should still work
        result = runner.invoke("scaffold", "defs", "foo_bar.components.baz.Baz", "qux")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()


@pytest.mark.parametrize(
    "selection",
    ["", "1", "2", "3", "n", "a"],
    ids=["default", "explicit_1", "explicit_2", "out_of_bounds", "quit", "invalid"],
)
def test_scaffold_defs_component_substring_multiple_match_success(selection: str) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "AssetComponent",
            "qux",
            input=f"{selection}\n",
        )
        if selection in ["", "1", "2"]:
            assert_runner_result(result)
            assert Path("src/foo_bar/defs/qux").exists()
            defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
            assert defs_yaml_path.exists()
            full_type = (
                "dagster_test.components.SimpleAssetComponent"
                if selection == "2"
                else "dagster_test.components.ComplexAssetComponent"
            )
            assert f"type: {full_type}" in defs_yaml_path.read_text()
        elif selection in ["3", "a"]:
            assert_runner_result(result, exit_0=False)
            assert "Did you mean one of these" in result.output
            assert "Invalid selection" in result.output
        elif selection == "n":
            assert_runner_result(result)
            assert "Did you mean one of these" in result.output
            assert "Exiting." in result.output


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_defs_component_json_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--json-params",
            '{"asset_key": "foo", "filename": "hello.py"}',
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        assert Path("src/foo_bar/defs/qux/hello.py").exists()
        defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
        assert defs_yaml_path.exists()
        assert (
            "type: dagster_test.components.SimplePipesScriptComponent" in defs_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_defs_component_key_value_params_success(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--asset-key=foo",
            "--filename=hello.py",
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/qux").exists()
        assert Path("src/foo_bar/defs/qux/hello.py").exists()
        defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
        assert defs_yaml_path.exists()
        assert (
            "type: dagster_test.components.SimplePipesScriptComponent" in defs_yaml_path.read_text()
        )


def test_scaffold_defs_component_json_params_and_key_value_params_fails() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster_test.components.SimplePipesScriptComponent",
            "qux",
            "--json-params",
            '{"filename": "hello.py"}',
            "--filename=hello.py",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Detected params passed as both --json-params and individual options" in result.output
        )


def test_scaffold_defs_component_undefined_component_type_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("scaffold", "defs", "fake.Fake", "qux")
        assert_runner_result(result, exit_0=False)
        assert "No registry object `fake.Fake` is registered" in result.output


def test_scaffold_defs_component_command_with_non_matching_module_name():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        #  move the module from foo_bar to module_not_same_as_project
        python_module = Path("src/foo_bar")
        python_module.rename("module_not_same_as_project")

        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert "Ensure folder `src/foo_bar/defs` exists in the project root." in str(
            result.exception
        )


@pytest.mark.parametrize("in_workspace", [True, False])
def test_scaffold_defs_component_already_exists_fails(in_workspace: bool) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace),
    ):
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_scaffold_defs_component_succeeds_non_default_defs_module() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        alt_defs_path = Path("src/foo_bar/_defs")
        alt_defs_path.mkdir(parents=True)
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "defs_module"), "foo_bar._defs")
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/_defs/qux").exists()
        defs_yaml_path = Path("src/foo_bar/_defs/qux/defs.yaml")
        assert defs_yaml_path.exists()
        assert (
            "type: dagster_test.components.AllMetadataEmptyComponent" in defs_yaml_path.read_text()
        )


def test_scaffold_defs_component_fails_defs_module_does_not_exist() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "defs_module"), "foo_bar._defs")
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert_runner_result(result, exit_0=False)
        assert "Ensure folder `src/foo_bar/_defs` exists in the project root." in str(
            result.exception
        )


def test_scaffold_defs_component_succeeds_scaffolded_component_type() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            runner.invoke("scaffold", "component", "Baz")
            assert Path("src/foo_bar/components/baz.py").exists()

            subprocess.run(
                ["dg", "scaffold", "defs", "foo_bar.components.baz.Baz", "qux"], check=True
            )
            assert Path("src/foo_bar/defs/qux").exists()
            defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
            assert defs_yaml_path.exists()
            assert "type: foo_bar.components.baz.Baz" in defs_yaml_path.read_text()


# Make sure that we can always refer to a component in its defining module
def test_scaffold_defs_component_succeeds_scaffolded_component_type_defining_module() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, uv_sync=True) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(["dg", "scaffold", "component", "Baz"], check=True)
            # runner.invoke("scaffold", "component", "Baz")
            # assert_runner_result(runner.invoke("scaffold", "component", "Baz"))
            component_path = Path("src/foo_bar/components/baz.py")
            assert component_path.exists()

            # We scaffolded at foo_bar.components.baz, so that is what has been added as a registry module. We are now
            # going to move the actual definition into a separate module, and ensure that we can
            # still reference our component by its defining module reference, even though this
            # module is not in the registry.
            component_path.rename("src/foo_bar/baz.py")
            component_path.write_text(
                textwrap.dedent("""
                from foo_bar.baz import Baz
            """)
            )

            # target the defining module foo_bar.baz, not the registry module foo_bar.components.baz
            subprocess.run(["dg", "scaffold", "defs", "foo_bar.baz.Baz", "qux"], check=True)
            assert Path("src/foo_bar/defs/qux").exists()
            defs_yaml_path = Path("src/foo_bar/defs/qux/defs.yaml")
            assert defs_yaml_path.exists()

            # The canonical name is still used in the scaffolded defs.yaml
            assert "type: foo_bar.components.baz.Baz" in defs_yaml_path.read_text()


# ########################
# ##### DEFS INLINE-COMPONENT
# ########################


def test_scaffold_defs_inline_component_success() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "inline-component",
            "inline/my_component",
            "--typename",
            "CustomType",
        )
        assert_runner_result(result)

        # Check directory and files exist
        component_path = Path("src/foo_bar/defs/inline/my_component")
        assert component_path.exists()

        component_file = component_path / "custom_type.py"
        assert component_file.exists()

        defs_file = component_path / "defs.yaml"
        assert defs_file.exists()

        # Check component file content
        expected_component_content = "\n".join(
            [
                "import dagster as dg",
                "",
                "class CustomType(dg.Component, dg.Model, dg.Resolvable):",
                "    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:",
                "        return dg.Definitions()",
            ]
        )

        assert component_file.read_text() == expected_component_content

        # Check defs.yaml content
        expected_defs_content = (
            "type: foo_bar.defs.inline.my_component.custom_type.CustomType\nattributes: {}"
        )
        assert defs_file.read_text() == expected_defs_content

        # Ensure it executes.
        result = runner.invoke("list", "defs")
        assert_runner_result(result)


def test_scaffold_defs_inline_component_with_superclass_success() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "inline-component",
            "inline/with_superclass",
            "--typename",
            "CustomComponent",
            "--superclass",
            "dagster_test.components.AllMetadataEmptyComponent",
        )
        assert_runner_result(result)

        # Check directory and files exist
        component_path = Path("src/foo_bar/defs/inline/with_superclass")
        assert component_path.exists()

        component_file = component_path / "custom_component.py"
        assert component_file.exists()

        defs_file = component_path / "defs.yaml"
        assert defs_file.exists()

        # Check component file content with superclass
        expected_component_content = "\n".join(
            [
                "import dagster as dg",
                "from dagster_test.components import AllMetadataEmptyComponent",
                "",
                "class CustomComponent(AllMetadataEmptyComponent):",
                "    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:",
                "        return dg.Definitions()",
            ]
        )

        assert component_file.read_text() == expected_component_content

        # Check defs.yaml content
        expected_defs_content = "type: foo_bar.defs.inline.with_superclass.custom_component.CustomComponent\nattributes: {}"
        assert defs_file.read_text() == expected_defs_content

        # Ensure it executes.
        result = runner.invoke("list", "defs")
        assert_runner_result(result)


def test_scaffold_defs_inline_component_existing_parent_directory() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        # Create the directory structure first
        Path("src/foo_bar/defs/inline/existing").mkdir(parents=True, exist_ok=True)

        result = runner.invoke(
            "scaffold",
            "defs",
            "inline-component",
            "inline/existing/component",
            "--typename",
            "ExistingDirComponent",
        )
        assert_runner_result(result)

        # Check directory and files exist
        component_path = Path("src/foo_bar/defs/inline/existing/component")
        assert component_path.exists()

        component_file = component_path / "existing_dir_component.py"
        assert component_file.exists()

        defs_file = component_path / "defs.yaml"
        assert defs_file.exists()

        # Check component file content
        expected_component_content = "\n".join(
            [
                "import dagster as dg",
                "",
                "class ExistingDirComponent(dg.Component, dg.Model, dg.Resolvable):",
                "    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:",
                "        return dg.Definitions()",
            ]
        )

        assert component_file.read_text() == expected_component_content

        # Check defs.yaml content
        expected_defs_content = "type: foo_bar.defs.inline.existing.component.existing_dir_component.ExistingDirComponent\nattributes: {}"
        assert defs_file.read_text() == expected_defs_content

        # Ensure it executes.
        result = runner.invoke("list", "defs")
        assert_runner_result(result)


def test_scaffold_defs_inline_component_already_exists_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        # Create a component first
        result = runner.invoke(
            "scaffold",
            "defs",
            "inline-component",
            "inline/my_component",
            "--typename",
            "CustomType",
        )
        assert_runner_result(result)

        # Try to create it again - should fail
        result = runner.invoke(
            "scaffold",
            "defs",
            "inline-component",
            "inline/my_component",
            "--typename",
            "AnotherType",
        )
        assert_runner_result(result, exit_0=False)

        # Check that the error message contains the right information
        assert "already exists" in result.output


# ##### SHIMS


def test_scaffold_defs_asset() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", "dagster.asset", "assets/foo.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/assets/foo.py").exists()
        assert Path("src/foo_bar/defs/assets/foo.py").read_text().startswith("import dagster as dg")
        assert not Path("src/foo_bar/defs/assets/foo.py").is_dir()
        assert not Path("src/foo_bar/defs/assets/defs.yaml").exists()

        result = runner.invoke("scaffold", "defs", "dagster.asset", "assets/bar.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/assets/bar.py").exists()
        assert not Path("src/foo_bar/defs/assets/defs.yaml").exists()


def test_scaffold_defs_asset_check_with_key() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster.asset_check",
            "asset_checks/my_check.py",
            "--asset-key=my/key",
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/asset_checks/my_check.py").exists()
        # check is uncommented if pointed at an asset
        assert (
            Path("src/foo_bar/defs/asset_checks/my_check.py")
            .read_text()
            .startswith("import dagster as dg")
        )
        assert (
            "asset=dg.AssetKey(['my', 'key'])"
            in Path("src/foo_bar/defs/asset_checks/my_check.py").read_text()
        )
        assert not Path("src/foo_bar/defs/asset_checks/my_check.py").is_dir()
        assert not Path("src/foo_bar/defs/asset_checks/defs.yaml").exists()

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        assert "my_check" in result.output


def test_scaffold_defs_bad_extension() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", "dagster.asset", "assets/foo")
        assert_runner_result(result, exit_0=False)


def test_scaffold_defs_multi_asset_basic() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke(
            "scaffold", "defs", "dagster.multi_asset", "multi_assets/composite.py"
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/multi_assets/composite.py").exists()
        assert (
            Path("src/foo_bar/defs/multi_assets/composite.py")
            .read_text()
            .startswith("import dagster as dg")
        )
        assert "@dg.multi_asset" in Path("src/foo_bar/defs/multi_assets/composite.py").read_text()
        asset_content = Path("src/foo_bar/defs/multi_assets/composite.py").read_text()
        assert "dg.AssetSpec(key=dg.AssetKey(['composite', 'first_asset']))" in asset_content
        assert "dg.AssetSpec(key=dg.AssetKey(['composite', 'second_asset']))" in asset_content
        assert not Path("src/foo_bar/defs/multi_assets/composite.py").is_dir()
        assert not Path("src/foo_bar/defs/multi_assets/defs.yaml").exists()

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = result.output
        assert "composite/first_asset" in output
        assert "composite/second_asset" in output


def test_scaffold_defs_multi_asset_params() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        # First, try scaffolding with multiple options using --asset-key
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster.multi_asset",
            "multi_assets/custom_keys.py",
            "--asset-key",
            "orders",
            "--asset-key",
            "customers",
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/multi_assets/custom_keys.py").exists()
        asset_content = Path("src/foo_bar/defs/multi_assets/custom_keys.py").read_text()
        assert "dg.AssetSpec(key=dg.AssetKey(['orders']))" in asset_content
        assert "dg.AssetSpec(key=dg.AssetKey(['customers']))" in asset_content

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = result.output
        assert "orders" in output
        assert "customers" in output

        # Next, try more complex keys with --json-params
        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster.multi_asset",
            "multi_assets/with_nested_keys.py",
            "--json-params",
            '{"asset_key": ["foo/bar", "baz/qux"]}',
        )
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/multi_assets/with_nested_keys.py").exists()
        asset_content = Path("src/foo_bar/defs/multi_assets/with_nested_keys.py").read_text()
        assert "dg.AssetSpec(key=dg.AssetKey(['foo', 'bar']))" in asset_content
        assert "dg.AssetSpec(key=dg.AssetKey(['baz', 'qux']))" in asset_content

        result = runner.invoke("list", "defs")
        assert_runner_result(result)
        output = result.output
        assert "foo/bar" in output
        assert "baz/qux" in output


def test_scaffold_defs_job() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", "dagster.job", "jobs/my_pipeline.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/jobs/my_pipeline.py").exists()
        assert (
            Path("src/foo_bar/defs/jobs/my_pipeline.py")
            .read_text()
            .startswith("import dagster as dg")
        )
        assert "@dg.job" in Path("src/foo_bar/defs/jobs/my_pipeline.py").read_text()
        job_content = Path("src/foo_bar/defs/jobs/my_pipeline.py").read_text()
        # Check for simple job scaffolding
        assert "pass" in job_content
        assert not Path("src/foo_bar/defs/jobs/my_pipeline.py").is_dir()
        assert not Path("src/foo_bar/defs/jobs/defs.yaml").exists()

        # Create another job file to verify it works consistently
        result = runner.invoke("scaffold", "defs", "dagster.job", "jobs/another_job.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/jobs/another_job.py").exists()


def test_scaffold_defs_sensor() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", "dagster.sensor", "my_sensor.py")
        assert_runner_result(result)
        assert Path("src/foo_bar/defs/my_sensor.py").exists()
        assert not Path("src/foo_bar/defs/defs.yaml").exists()


# ########################
# ##### DEFS OPTIONS
# ########################


def test_scaffold_defs_json_params_option_only_for_scaffold_params() -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        # SimplePipesScriptComponent has scaffold params, so --json-params should be defined
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.SimplePipesScriptComponent", "--help"
        )
        assert_runner_result(result)
        assert "--json-params" in result.output

        # AllMetadataEmptyComponent does not have scaffold params, so --json-params should not be
        # defined
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "--help"
        )
        assert_runner_result(result)
        assert "--json-params" not in result.output


def test_scaffold_defs_format_option_only_for_components() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "defs", "dagster.DefsFolderComponent", "--help")
        assert_runner_result(result)
        assert "--format" in result.output

        # `asset` is not a component, so --format should not be defined
        result = runner.invoke("scaffold", "defs", "dagster.asset", "--help")
        assert_runner_result(result)
        assert "--format" not in result.output


# ##### REAL COMPONENTS


dbt_project_path = Path("../stub_projects/dbt_project_location/defs/jaffle_shop")


@pytest.mark.parametrize(
    "params",
    [
        ["--json-params", json.dumps({"project_path": str(dbt_project_path)})],
        ["--project-path", str(dbt_project_path)],
    ],
)
def test_scaffold_dbt_project_instance(params) -> None:
    project_kwargs: dict[str, Any] = {"use_editable_dagster": True}

    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, uv_sync=True, **project_kwargs) as project_path,
    ):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-dbt"], check=True)

        with activate_venv(project_path / ".venv"):
            subprocess.run(
                [
                    "dg",
                    "scaffold",
                    "defs",
                    "dagster_dbt.DbtProjectComponent",
                    "my_project",
                    *params,
                ],
                check=True,
            )
            assert Path("src/foo_bar/defs/my_project").exists()

            defs_yaml_path = Path("src/foo_bar/defs/my_project/defs.yaml")
            assert defs_yaml_path.exists()
            assert "type: dagster_dbt.DbtProjectComponent" in defs_yaml_path.read_text()
            assert (
                cross_platfrom_string_path("stub_projects/dbt_project_location/defs/jaffle_shop")
                in defs_yaml_path.read_text()
            )


# ########################
# ##### COMPONENT
# ########################


def test_scaffold_component_type_success() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        subprocess.run(["dg", "scaffold", "component", "Baz"], check=True)
        assert Path("src/foo_bar/components/baz.py").exists()

        result = subprocess.run(
            ["dg", "list", "components", "--json"], check=True, capture_output=True
        )
        result_json = json.loads(result.stdout.decode("utf-8"))

        assert any(json_entry["key"] == "foo_bar.components.Baz" for json_entry in result_json)

        assert (
            Path("src/foo_bar/components/__init__.py").read_text().strip()
            == textwrap.dedent("""
            from foo_bar.components.baz import Baz as Baz
        """).strip()
        )


def test_scaffold_component_type_already_exists_fails() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(runner),
    ):
        subprocess.run(["dg", "scaffold", "component", "Baz"], check=True)

        result = subprocess.run(
            ["dg", "scaffold", "component", "Baz"], check=False, capture_output=True, text=True
        )

        assert result.returncode != 0
        assert "already exists" in result.stderr


def test_scaffold_component_type_succeeds_non_default_component_components_package() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_component_library_foo_bar(
            runner, components_module_name="foo_bar._components"
        ),
    ):
        subprocess.run(["dg", "scaffold", "component", "Baz"], check=True)
        assert Path("src/foo_bar/_components/baz.py").exists()

        result = subprocess.run(
            ["dg", "list", "components", "--json"], check=True, capture_output=True
        )
        result_json = json.loads(result.stdout.decode("utf-8"))

        assert any(json_entry["key"] == "foo_bar._components.Baz" for json_entry in result_json)


def test_scaffold_component_succeeds_scaffolded_no_model() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("scaffold", "component", "Baz", "--no-model")
        assert_runner_result(result)
        assert Path("src/foo_bar/components/baz.py").exists()

        output = textwrap.dedent('''
            import dagster as dg

            class Baz(dg.Component, dg.Resolvable):
                """COMPONENT SUMMARY HERE.

                COMPONENT DESCRIPTION HERE.
                """

                def __init__(
                    self,
                    # added params here define needed arguments when instantiated in Python, and yaml schema via Resolvable
                ):
                    pass

                def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
                    # Add definition construction logic here.
                    return dg.Definitions()
        ''').strip()

        assert Path("src/foo_bar/components/baz.py").read_text().strip() == output


@pytest.mark.parametrize(
    "component_name",
    [
        "foo_bar.components.baz.Baz",
        "foo_bar._components.baz.Baz",
        "Baz",
    ],
    ids=[
        "with_module_in_default",
        "with_module_in_alternative",
        "class_name_only",
    ],
)
def test_scaffold_component_no_entry_point_success(
    component_name: str,
) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner),
    ):
        if "." not in component_name:
            component_key = "foo_bar.components.baz.Baz"
        else:
            component_key = component_name

        result = runner.invoke("scaffold", "component", component_name)
        assert_runner_result(result)
        importlib.invalidate_caches()  # Needed to make sure new submodule is discoverable

        component_module = component_key.rsplit(".", 1)[0]
        module_file = (Path("src") / "/".join(component_module.split("."))).with_suffix(".py")
        assert module_file.exists()

        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        result_json = json.loads(result.output)

        assert any(json_entry["key"] == component_key for json_entry in result_json)

        # Only the module that adds to the _component will add a line to registry modules. That's
        # because the other cases are already covered by the default scaffolded wildcard
        # `foo_bar.components.*`.
        expected_registry_modules = [
            "foo_bar.components.*",
        ]
        if "_components" in component_name:
            expected_registry_modules.append("foo_bar._components.baz")
        registry_modules_str = "\n".join(
            [
                "registry_modules = [",
                *[f'    "{module}",' for module in expected_registry_modules],
                "]",
            ]
        )
        pyproject_toml = Path("pyproject.toml").read_text()
        assert registry_modules_str in pyproject_toml
