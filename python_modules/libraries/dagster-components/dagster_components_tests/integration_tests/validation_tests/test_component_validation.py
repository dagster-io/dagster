import shutil
import tempfile
from pathlib import Path

import pytest
from dagster._core.definitions.definitions_class import Definitions
from pydantic import ValidationError

from dagster_components_tests.integration_tests.component_loader import (
    build_defs_from_component_path,
    load_test_component_project_context,
)


def load_test_component_defs_inject_component(path: str, component_to_inject: Path) -> Definitions:
    origin_path = Path(__file__).parent.parent / "components" / path

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(origin_path, tmpdir, dirs_exist_ok=True)
        shutil.copy(component_to_inject, Path(tmpdir) / "__init__.py")

        context = load_test_component_project_context()
        return build_defs_from_component_path(
            path=Path(tmpdir),
            registry=context.component_registry,
            resources={},
        )


def test_basic_component_success() -> None:
    load_test_component_defs_inject_component(
        "validation/basic_component_success", Path(__file__).parent / "basic_components.py"
    )


def test_basic_component_invalid_value() -> None:
    with pytest.raises(ValidationError) as e:
        load_test_component_defs_inject_component(
            "validation/basic_component_invalid_value",
            Path(__file__).parent / "basic_components.py",
        )

    assert "component.yaml:5" in str(e.value)
    assert "params.an_int" in str(e.value)
    assert "Input should be a valid integer" in str(e.value)


def test_basic_component_missing_value() -> None:
    with pytest.raises(ValidationError) as e:
        load_test_component_defs_inject_component(
            "validation/basic_component_missing_value",
            Path(__file__).parent / "basic_components.py",
        )

    # Points to the lowest element in the hierarchy which is missing a required field
    assert "component.yaml:4" in str(e.value)
    assert "params.an_int" in str(e.value)
    assert "Field required" in str(e.value)


def test_nested_component_invalid_values() -> None:
    with pytest.raises(ValidationError) as e:
        load_test_component_defs_inject_component(
            "validation/nested_component_invalid_values",
            Path(__file__).parent / "basic_components.py",
        )

    assert "component.yaml:7" in str(e.value)
    assert "Input should be a valid integer" in str(e.value)
    assert "params.nested.foo.an_int" in str(e.value)
    assert "component.yaml:12" in str(e.value)
    assert "Input should be a valid string" in str(e.value)


def test_nested_component_missing_value() -> None:
    with pytest.raises(ValidationError) as e:
        load_test_component_defs_inject_component(
            "validation/nested_component_missing_values",
            Path(__file__).parent / "basic_components.py",
        )

    assert "component.yaml:6" in str(e.value)
    assert "Field required" in str(e.value)
    assert "component.yaml:11" in str(e.value)
