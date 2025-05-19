from pathlib import Path

from dagster.components.test.build import defs_relative_component_context


def dagster_test_root() -> Path:
    python_modules = Path(__file__).parent.parent.parent.parent.parent
    return python_modules / "dagster-test"


def dagster_test_defs_module() -> Path:
    return dagster_test_root() / "dagster_test" / "dg_defs"


def test_basic_build_component_and_defs() -> None:
    python_modules = Path(__file__).parent.parent.parent.parent.parent
    assert python_modules.name == "python_modules"

    dagster_test_path = python_modules / "dagster-test"
    assert dagster_test_path.exists()
    assert (dagster_test_path / "setup.py").exists()
    defs_relative_component_context(
        project_root=dagster_test_root(),
        defs_path=dagster_test_defs_module(),
        defs_module_name="dagster_test.dg_defs",
    )
