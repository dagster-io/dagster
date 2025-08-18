from pathlib import Path

import pytest
import yaml

# Import the YAML generation functions from CLI
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)

# Import the component classes directly
from dagster_test.components import SimplePipesScriptComponent

# Path to test data files for validation
TEST_DATA_DIR = Path(__file__).parent.parent / "yaml_template" / "test_data"

# Component test cases
TEST_COMPONENTS = [
    {
        "name": "simple_example",
        "component_class": SimplePipesScriptComponent,
        "test_data_dir": "simple_example",
    },
    # Note: Other components require additional dependencies that may not be available in test environment
    # They can be added when those dependencies are confirmed to be available
]


def _get_component_schema(component_class: type) -> dict:
    """Get the JSON schema for a component class."""
    model_cls = component_class.get_model_cls()
    if model_cls is None:
        return {}
    return model_cls.model_json_schema()


def _get_component_type_str(component_class: type) -> str:
    """Get the component type string for a component class."""
    return f"{component_class.__module__}.{component_class.__name__}"


@pytest.mark.parametrize("test_case", TEST_COMPONENTS)
def test_defs_yaml_schema_matches_test_data(test_case):
    """Test that generated YAML schema matches expected test data."""
    component_class = test_case["component_class"]
    test_data_path = TEST_DATA_DIR / test_case["test_data_dir"] / "expected_schema"

    # Skip if test data doesn't exist
    if not test_data_path.exists():
        pytest.skip(f"No expected_schema file for {test_case['name']}")

    # Generate YAML schema using the same function the CLI uses
    component_type_str = _get_component_type_str(component_class)
    component_schema = _get_component_schema(component_class)
    generated_yaml = generate_defs_yaml_schema(component_type_str, component_schema)

    # Load expected content
    expected_yaml = test_data_path.read_text().strip()

    assert generated_yaml.strip() == expected_yaml


@pytest.mark.parametrize("test_case", TEST_COMPONENTS)
def test_defs_yaml_example_values_matches_test_data(test_case):
    """Test that generated YAML example values match expected test data."""
    component_class = test_case["component_class"]
    test_data_path = TEST_DATA_DIR / test_case["test_data_dir"] / "expected_example"

    # Skip if test data doesn't exist
    if not test_data_path.exists():
        pytest.skip(f"No expected_example file for {test_case['name']}")

    # Generate YAML example values using the same function the CLI uses
    component_type_str = _get_component_type_str(component_class)
    component_schema = _get_component_schema(component_class)
    generated_yaml = generate_defs_yaml_example_values(component_type_str, component_schema)

    # Load expected content
    expected_yaml = test_data_path.read_text().strip()

    assert generated_yaml.strip() == expected_yaml


@pytest.mark.parametrize("test_case", TEST_COMPONENTS)
def test_generated_yaml_is_valid(test_case):
    """Test that both generated schema and example YAML are syntactically valid."""
    component_class = test_case["component_class"]
    component_type_str = _get_component_type_str(component_class)
    component_schema = _get_component_schema(component_class)

    # Test schema YAML (filter out comments)
    schema_yaml = generate_defs_yaml_schema(component_type_str, component_schema)
    schema_lines = [line for line in schema_yaml.split("\n") if not line.strip().startswith("#")]
    schema_content = "\n".join(schema_lines)

    try:
        yaml.safe_load(schema_content)
    except yaml.YAMLError as e:
        pytest.fail(f"Generated schema YAML is invalid for {test_case['name']}: {e}")

    # Test example YAML
    example_yaml = generate_defs_yaml_example_values(component_type_str, component_schema)
    try:
        parsed_example = yaml.safe_load(example_yaml)
        assert "type" in parsed_example
        assert "attributes" in parsed_example
    except yaml.YAMLError as e:
        pytest.fail(f"Generated example YAML is invalid for {test_case['name']}: {e}")


def test_component_type_strings_are_correct():
    """Test that component type strings match the expected format."""
    for test_case in TEST_COMPONENTS:
        component_class = test_case["component_class"]
        component_type_str = _get_component_type_str(component_class)
        component_schema = _get_component_schema(component_class)

        generated_schema = generate_defs_yaml_schema(component_type_str, component_schema)
        generated_example = generate_defs_yaml_example_values(component_type_str, component_schema)

        # Extract component type from generated YAML
        expected_type = f"{component_class.__module__}.{component_class.__name__}"

        # Check schema contains correct type
        assert f"type: {expected_type}" in generated_schema

        # Check example contains correct type
        assert f'type: "{expected_type}"' in generated_example


@pytest.mark.parametrize("test_case", TEST_COMPONENTS)
def test_schema_has_required_structure(test_case):
    """Test that generated schema has the expected structure elements."""
    component_class = test_case["component_class"]
    component_type_str = _get_component_type_str(component_class)
    component_schema = _get_component_schema(component_class)
    generated_yaml = generate_defs_yaml_schema(component_type_str, component_schema)

    # Should contain template comment
    assert "# Template with instructions" in generated_yaml

    # Should contain type and attributes sections
    assert "type:" in generated_yaml
    assert "attributes:" in generated_yaml

    # Should contain field type hints
    assert "<" in generated_yaml and ">" in generated_yaml

    # Should contain Required/Optional annotations
    assert "Required" in generated_yaml or "Optional" in generated_yaml


def test_all_test_data_files_correspond_to_components():
    """Ensure all test data directories have corresponding component definitions."""
    test_data_dirs = {d.name for d in TEST_DATA_DIR.iterdir() if d.is_dir()}
    component_test_dirs = {tc["test_data_dir"] for tc in TEST_COMPONENTS}

    # Note: It's okay to have more test data than components we test, since some
    # components may require dependencies not available in the test environment
    missing_test_data = component_test_dirs - test_data_dirs
    if missing_test_data:
        pytest.fail(f"Component definitions without test data directories: {missing_test_data}")
