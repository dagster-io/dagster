import importlib
import json
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from dagster_dg_core.utils import activate_venv, create_toml_node, modify_toml_as_dict, pushd
from dagster_shared.ipc import interrupt_ipc_subprocess
from dagster_test.components.test_utils.test_cases import (
    BASIC_COMPONENT_TYPE_FILEPATH,
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    BASIC_VALID_VALUE,
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
    msg_includes_all_of,
)
from dagster_test.dg_utils.utils import (
    COMPONENT_INTEGRATION_TEST_DIR,
    ProxyRunner,
    assert_runner_result,
    create_project_from_components,
)

ENV_VAR_TEST_CASES = [
    ComponentValidationTestCase(
        component_path="validation/basic_component_missing_declared_env",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        check_error_msg=msg_includes_all_of(
            "defs.yaml:1",
            "Component uses environment variables that are not specified in the component file: AN_INT, A_STRING",
        ),
    ),
]

CLI_TEST_CASES = [
    *COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase(
        component_path="validation/basic_component_missing_type",
        component_type_filepath=None,
        should_error=True,
        check_error_msg=msg_includes_all_of(
            "defs.yaml:1",
            "Component type 'foo_bar.defs.basic_component_missing_type.MyComponentDoesNotExist' not found",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/basic_component_extra_top_level_value",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        check_error_msg=msg_includes_all_of(
            "defs.yaml:7",
            "'an_extra_top_level_value' was unexpected",
        ),
    ),
    *ENV_VAR_TEST_CASES,
]


@pytest.mark.parametrize(
    "test_case",
    CLI_TEST_CASES,
    ids=[str(case.component_path) for case in CLI_TEST_CASES],
)
def test_check_yaml(test_case: ComponentValidationTestCase) -> None:
    """Tests that the check CLI prints rich error messages when attempting to
    load components with errors.
    """
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            test_case.component_path,
            local_component_defn_to_inject=test_case.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(tmpdir):
            # Enable validation for ENV_VAR_TEST_CASES since default is now False
            cmd_args = ["check", "yaml"]
            if test_case in ENV_VAR_TEST_CASES:
                cmd_args.append("--validate-requirements")
            result = runner.invoke(*cmd_args)
            if test_case.should_error:
                assert_runner_result(result, exit_0=False)
                assert test_case.check_error_msg
                test_case.check_error_msg(str(result.stdout))

            else:
                assert_runner_result(result)


@pytest.mark.parametrize(
    "test_case",
    ENV_VAR_TEST_CASES,
    ids=[str(case.component_path) for case in ENV_VAR_TEST_CASES],
)
def test_check_yaml_no_env_var_validation(test_case: ComponentValidationTestCase) -> None:
    """Tests that the check CLI does not validate env vars when the --no-validate-requirements flag is provided (default)."""
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            test_case.component_path,
            local_component_defn_to_inject=test_case.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(tmpdir):
            # Test both default behavior (no validation) and explicit --no-validate-requirements
            result_default = runner.invoke("check", "yaml")
            assert_runner_result(result_default)

            result_explicit = runner.invoke("check", "yaml", "--no-validate-requirements")
            assert_runner_result(result_explicit)


def test_check_yaml_succeeds_non_default_defs_module() -> None:
    with ProxyRunner.test() as runner, create_project_from_components(runner):
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "defs_module"), "foo_bar._defs")

        # We need to do all of this copying here rather than relying on the project setup
        # fixture because that fixture assumes a default component package.
        component_src_path = COMPONENT_INTEGRATION_TEST_DIR / BASIC_VALID_VALUE.component_path
        component_name = component_src_path.name
        defs_dir = Path.cwd() / "src" / "foo_bar" / "_defs" / component_name
        defs_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(component_src_path, defs_dir, dirs_exist_ok=True)
        assert BASIC_VALID_VALUE.component_type_filepath
        shutil.copy(BASIC_VALID_VALUE.component_type_filepath, defs_dir / "__init__.py")

        result = runner.invoke("check", "yaml")
        assert_runner_result(result, exit_0=True)


def test_check_yaml_succeeds_unregistered_component() -> None:
    """Ensure that a valid python symbol reference to a component type still works even if it is not registered."""
    with ProxyRunner.test() as runner, create_project_from_components(runner):
        result = runner.invoke("scaffold", "component", "Baz")
        assert_runner_result(result, exit_0=True)
        importlib.invalidate_caches()  # Ensure component discovery not blocked by python import cache

        # Create component instance
        result = runner.invoke("scaffold", "defs", "foo_bar.components.baz.Baz", "qux")
        assert_runner_result(result, exit_0=True)

        # Remove registry module entry that would make the newly scaffolded component discoverable
        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(toml_dict, ("tool", "dg", "project", "registry_modules"), [])

        # Make sure the new component is not registered
        result = runner.invoke("list", "components", "--json")
        assert_runner_result(result)
        component_keys = [c["key"] for c in json.loads(result.stdout)]
        assert "foo_bar.components.baz.Baz" not in component_keys

        # Check YAML should pass anyway, since we support unregistered components
        result = runner.invoke("check", "yaml")
        assert_runner_result(result)


def test_actionable_error_message_no_defs_check_yaml():
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_VALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_VALID_VALUE.component_type_filepath,
            uv_sync=True,
        ) as tmpdir,
        pushd(tmpdir),
        activate_venv(tmpdir / ".venv"),
    ):
        shutil.rmtree(Path("src") / "foo_bar" / "defs")

        Path(".env").write_text("FOO=bar")
        result = runner.invoke("check", "yaml")
        assert_runner_result(result, exit_0=False)
        assert "Ensure folder `src/foo_bar/defs` exists in the project root." in str(
            str(result.exception)
        )

        with modify_toml_as_dict(Path("pyproject.toml")) as toml_dict:
            create_toml_node(
                toml_dict, ("tool", "dg", "project", "defs_module"), "foo_bar.other_defs"
            )

        result = runner.invoke("check", "yaml")
        assert_runner_result(result, exit_0=False)
        assert "Ensure folder `src/foo_bar/other_defs` exists in the project root." in str(
            str(result.exception)
        )


def test_check_yaml_with_watch() -> None:
    """Tests that the check CLI prints rich error messages when attempting to
    load components with errors.
    """
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_VALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_VALID_VALUE.component_type_filepath,
            uv_sync=True,
        ) as tmpdir_valid,
        create_project_from_components(
            runner,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_INVALID_VALUE.component_type_filepath,
            uv_sync=True,
        ) as tmpdir,
    ):
        with pushd(tmpdir), activate_venv(tmpdir / ".venv"):
            check_process = subprocess.Popen(
                ["dg", "check", "yaml", "--watch"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            time.sleep(10)  # Give the check command time to start

            # Copy the invalid component into the valid code location
            shutil.copy(
                tmpdir_valid / "src" / "foo_bar" / "defs" / "basic_component_success" / "defs.yaml",
                tmpdir / "src" / "foo_bar" / "defs" / "basic_component_invalid_value" / "defs.yaml",
            )

            time.sleep(10)  # Give time for the watcher to detect changes

            # Signal the watcher to exit
            interrupt_ipc_subprocess(check_process)

            stdout, stderr = check_process.communicate()

            assert "All component YAML validated successfully" in stdout.decode("utf-8")
            assert BASIC_INVALID_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(stdout.decode("utf-8"))


@pytest.mark.parametrize(
    "scope_check_run",
    [True, False],
)
def test_check_yaml_multiple_components(scope_check_run: bool) -> None:
    """Ensure that the check CLI can validate multiple components in a single project, and
    that error messages from all components are displayed.

    The parameter `scope_check_run` determines whether the check CLI is run pointing at both
    components or none (defaulting to the entire workspace) - the output should be the same in
    either case, this just tests that the CLI can handle multiple filters.
    """
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke(
                "check",
                "yaml",
                *(
                    [
                        str(Path("src") / "foo_bar" / "defs" / "basic_component_missing_value"),
                        str(Path("src") / "foo_bar" / "defs" / "basic_component_invalid_value"),
                    ]
                    if scope_check_run
                    else []
                ),
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))


def test_check_yaml_multiple_components_filter() -> None:
    """Ensure that the check CLI filters components to validate based on the provided paths."""
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(tmpdir):
            result = runner.invoke(
                "check",
                "yaml",
                str(Path("src") / "foo_bar" / "defs" / "basic_component_missing_value"),
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg

            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))
            # We exclude the invalid value test case
            with pytest.raises(AssertionError):
                BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
