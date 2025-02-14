import contextlib
import re
import shutil
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import pytest
from dagster_components.test.test_cases import (
    BASIC_COMPONENT_TYPE_FILEPATH,
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    BASIC_VALID_VALUE,
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
    msg_includes_all_of,
)
from dagster_dg.utils import ensure_dagster_dg_tests_import, pushd, set_toml_value

ensure_dagster_dg_tests_import()
from dagster_dg.utils import filesystem
from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_foo_bar,
    modify_pyproject_toml,
)

COMPONENT_INTEGRATION_TEST_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "dagster-components"
    / "dagster_components_tests"
    / "integration_tests"
    / "components"
)

CLI_TEST_CASES = [
    *COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase(
        component_path="validation/basic_component_missing_type",
        component_type_filepath=None,
        should_error=True,
        check_error_msg=msg_includes_all_of(
            "component.yaml:1",
            "Component type 'my_component_does_not_exist@__init__.py' not found",
        ),
    ),
    ComponentValidationTestCase(
        component_path="validation/basic_component_extra_top_level_value",
        component_type_filepath=BASIC_COMPONENT_TYPE_FILEPATH,
        should_error=True,
        check_error_msg=msg_includes_all_of(
            "component.yaml:7",
            "'an_extra_top_level_value' was unexpected",
        ),
    ),
]


@contextlib.contextmanager
def create_code_location_from_components(
    runner: ProxyRunner,
    *src_paths: str,
    local_component_defn_to_inject: Optional[Path] = None,
) -> Iterator[Path]:
    """Scaffolds a code location with the given components in a temporary directory,
    injecting the provided local component defn into each component's __init__.py.
    """
    origin_paths = [COMPONENT_INTEGRATION_TEST_DIR / src_path for src_path in src_paths]
    with isolated_example_code_location_foo_bar(
        runner,
        component_dirs=origin_paths,
    ):
        for src_path in src_paths:
            components_dir = Path.cwd() / "foo_bar" / "components" / src_path.split("/")[-1]
            if local_component_defn_to_inject:
                shutil.copy(local_component_defn_to_inject, components_dir / "__init__.py")

        yield Path.cwd()


def test_component_check_succeeds_non_default_component_package() -> None:
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            runner,
        ),
    ):
        with modify_pyproject_toml() as toml:
            set_toml_value(toml, ("tool", "dg", "component_package"), "foo_bar._components")

        # We need to do all of this copying here rather than relying on the code location setup
        # fixture because that fixture assumes a default component package.
        component_src_path = COMPONENT_INTEGRATION_TEST_DIR / BASIC_VALID_VALUE.component_path
        component_name = component_src_path.name
        components_dir = Path.cwd() / "foo_bar" / "_components" / component_name
        components_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(component_src_path, components_dir, dirs_exist_ok=True)
        assert BASIC_VALID_VALUE.component_type_filepath
        shutil.copy(BASIC_VALID_VALUE.component_type_filepath, components_dir / "__init__.py")

        result = runner.invoke("component", "check")
        assert_runner_result(result, exit_0=True)


@pytest.mark.parametrize(
    "test_case",
    CLI_TEST_CASES,
    ids=[str(case.component_path) for case in CLI_TEST_CASES],
)
def test_validation_cli(test_case: ComponentValidationTestCase) -> None:
    """Tests that the check CLI prints rich error messages when attempting to
    load components with errors.
    """
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            runner,
            test_case.component_path,
            local_component_defn_to_inject=test_case.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(tmpdir):
            result = runner.invoke("component", "check")
            if test_case.should_error:
                assert result.exit_code != 0, str(result.stdout)

                assert test_case.check_error_msg
                test_case.check_error_msg(str(result.stdout))

            else:
                assert result.exit_code == 0


def test_check_cli_with_watch() -> None:
    """Tests that the check CLI prints rich error messages when attempting to
    load components with errors.
    """
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            runner,
            BASIC_VALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_VALID_VALUE.component_type_filepath,
        ) as tmpdir_valid,
        create_code_location_from_components(
            runner,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_INVALID_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(tmpdir):
            stdout = ""

            def run_check(runner: ProxyRunner) -> None:
                result = runner.invoke(
                    "component",
                    "check",
                    "--watch",
                    catch_exceptions=False,
                )
                nonlocal stdout
                stdout = result.stdout

            # Start the check command in a separate thread
            check_thread = threading.Thread(target=run_check, args=(runner,))
            check_thread.daemon = True  # Make thread daemon so it exits when main thread exits
            check_thread.start()

            time.sleep(2)  # Give the check command time to start

            # Copy the invalid component into the valid code location
            shutil.copy(
                tmpdir_valid
                / "foo_bar"
                / "components"
                / "basic_component_success"
                / "component.yaml",
                tmpdir
                / "foo_bar"
                / "components"
                / "basic_component_invalid_value"
                / "component.yaml",
            )

            time.sleep(2)  # Give time for the watcher to detect changes

            # Signal the watcher to exit
            filesystem.SHOULD_WATCHER_EXIT = True

            time.sleep(2)
            check_thread.join(timeout=1)

            assert "All components validated successfully" in stdout
            assert BASIC_INVALID_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(stdout)


@pytest.mark.parametrize(
    "scope_check_run",
    [True, False],
)
def test_validation_cli_multiple_components(scope_check_run: bool) -> None:
    """Ensure that the check CLI can validate multiple components in a single code location, and
    that error messages from all components are displayed.

    The parameter `scope_check_run` determines whether the check CLI is run pointing at both
    components or none (defaulting to the entire workspace) - the output should be the same in
    either case, this just tests that the CLI can handle multiple filters.
    """
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke(
                "component",
                "check",
                *(
                    [
                        str(Path("foo_bar") / "components" / "basic_component_missing_value"),
                        str(Path("foo_bar") / "components" / "basic_component_invalid_value"),
                    ]
                    if scope_check_run
                    else []
                ),
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))


def test_validation_cli_multiple_components_filter() -> None:
    """Ensure that the check CLI filters components to validate based on the provided paths."""
    with (
        ProxyRunner.test() as runner,
        create_code_location_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(tmpdir):
            result = runner.invoke(
                "component",
                "check",
                str(Path("foo_bar") / "components" / "basic_component_missing_value"),
            )
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg

            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))
            # We exclude the invalid value test case
            with pytest.raises(AssertionError):
                BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))


def test_validation_cli_local_component_cache() -> None:
    """Tests that the check CLI properly caches local components to avoid re-loading them."""
    with (
        ProxyRunner.test(verbose=True) as runner,
        create_code_location_from_components(
            runner,
            BASIC_VALID_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_VALID_VALUE.component_type_filepath,
        ) as code_location_dir,
    ):
        with pushd(code_location_dir):
            result = runner.invoke(
                "component",
                "check",
            )
            assert re.search(
                r"CACHE \[write\].*basic_component_success.*local_component_registry", result.stdout
            )
            assert re.search(
                r"CACHE \[write\].*basic_component_invalid_value.*local_component_registry",
                result.stdout,
            )

            # Local components should all be cached
            result = runner.invoke(
                "component",
                "check",
            )
            assert not re.search(
                r"CACHE \[write\].*basic_component_success.*local_component_registry", result.stdout
            )
            assert not re.search(
                r"CACHE \[write\].*basic_component_invalid_value.*local_component_registry",
                result.stdout,
            )

            # Update local component type, to invalidate cache
            contents = (
                code_location_dir
                / "foo_bar"
                / "components"
                / "basic_component_success"
                / "__init__.py"
            ).read_text()
            (
                code_location_dir
                / "foo_bar"
                / "components"
                / "basic_component_success"
                / "__init__.py"
            ).write_text(contents + "\n")

            # basic_component_success local component is now be invalidated and needs to be re-cached, the other one should still be cached
            result = runner.invoke(
                "component",
                "check",
            )
            assert re.search(
                r"CACHE \[write\].*basic_component_success.*local_component_registry", result.stdout
            )
            assert not re.search(
                r"CACHE \[write\].*basic_component_invalid_value.*local_component_registry",
                result.stdout,
            )
