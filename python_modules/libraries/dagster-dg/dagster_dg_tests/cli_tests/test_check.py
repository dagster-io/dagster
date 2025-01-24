import contextlib
import os
import re
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import pytest
from dagster_components.test.test_cases import (
    BASIC_INVALID_VALUE,
    BASIC_MISSING_VALUE,
    BASIC_VALID_VALUE,
    COMPONENT_VALIDATION_TEST_CASES,
    ComponentValidationTestCase,
    msg_includes_all_of,
)
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()
from dagster_dg_tests.utils import ProxyRunner, clear_module_from_cache

COMPONENT_INTEGRATION_TEST_DIR = (
    Path(__file__).parent.parent.parent.parent
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
            "Unable to locate local component type '.my_component_does_not_exist'",
        ),
    ),
]


@contextmanager
def new_cwd(path: str) -> Iterator[None]:
    old = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


@contextlib.contextmanager
def create_code_location_from_components(
    runner: ProxyRunner, *src_paths: str, local_component_defn_to_inject: Optional[Path] = None
) -> Iterator[Path]:
    """Scaffolds a code location with the given components in a temporary directory,
    injecting the provided local component defn into each component's __init__.py.
    """
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with tempfile.TemporaryDirectory() as tmpdir, new_cwd(tmpdir):
        runner.invoke(
            "code-location",
            "scaffold",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "my_location",
        )

        code_location_dir = Path(tmpdir) / "my_location"
        assert code_location_dir.exists()

        (code_location_dir / "lib").mkdir(parents=True, exist_ok=True)
        (code_location_dir / "lib" / "__init__.py").touch()
        for src_path in src_paths:
            component_name = src_path.split("/")[-1]

            components_dir = code_location_dir / "my_location" / "components" / component_name
            components_dir.mkdir(parents=True, exist_ok=True)

            origin_path = COMPONENT_INTEGRATION_TEST_DIR / src_path

            shutil.copytree(origin_path, components_dir, dirs_exist_ok=True)
            if local_component_defn_to_inject:
                shutil.copy(local_component_defn_to_inject, components_dir / "__init__.py")

        with clear_module_from_cache("my_location"):
            yield code_location_dir


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
        with new_cwd(str(tmpdir)):
            result = runner.invoke("component", "check")
            if test_case.should_error:
                assert result.exit_code != 0, str(result.stdout)

                assert test_case.check_error_msg
                test_case.check_error_msg(str(result.stdout))

            else:
                assert result.exit_code == 0


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
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                "component",
                "check",
                *(
                    [
                        str(Path("my_location") / "components" / "basic_component_missing_value"),
                        str(Path("my_location") / "components" / "basic_component_invalid_value"),
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
        with new_cwd(str(tmpdir)):
            result = runner.invoke(
                "component",
                "check",
                str(Path("my_location") / "components" / "basic_component_missing_value"),
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
        with new_cwd(str(code_location_dir)):
            result = runner.invoke("component", "check")
            assert re.search(
                r"CACHE \[write\].*basic_component_success.*local_component_registry", result.stdout
            )
            assert re.search(
                r"CACHE \[write\].*basic_component_invalid_value.*local_component_registry",
                result.stdout,
            )

            # Local components should all be cached
            result = runner.invoke("component", "check")
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
                / "my_location"
                / "components"
                / "basic_component_success"
                / "__init__.py"
            ).read_text()
            (
                code_location_dir
                / "my_location"
                / "components"
                / "basic_component_success"
                / "__init__.py"
            ).write_text(contents + "\n")

            # basic_component_success local component is now be invalidated and needs to be re-cached, the other one should still be cached
            result = runner.invoke("component", "check")
            assert re.search(
                r"CACHE \[write\].*basic_component_success.*local_component_registry", result.stdout
            )
            assert not re.search(
                r"CACHE \[write\].*basic_component_invalid_value.*local_component_registry",
                result.stdout,
            )
