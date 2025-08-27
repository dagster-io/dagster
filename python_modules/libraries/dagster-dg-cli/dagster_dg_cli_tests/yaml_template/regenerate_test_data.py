#!/usr/bin/env python3
"""Script to regenerate the YAML test data files for component inspection.

This script generates the expected_schema and expected_example files
that are used to test the YAML generation functionality.
"""

from pathlib import Path

# Import the YAML generation functions from CLI
from dagster_dg_cli.utils.yaml_template_generator import (
    generate_defs_yaml_example_values,
    generate_defs_yaml_schema,
)

# Import the component classes directly
from dagster_test.components import SimplePipesScriptComponent

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Component test cases - same as in the test file
TEST_COMPONENTS = [
    {
        "name": "simple_example",
        "component_class": SimplePipesScriptComponent,
        "test_data_dir": "simple_example",
    },
    # Add more components here as they become available in the test environment
]


def get_component_schema(component_class: type) -> dict:
    """Get the JSON schema for a component class."""
    model_cls = component_class.get_model_cls()
    if model_cls is None:
        return {}
    return model_cls.model_json_schema()


def get_component_type_str(component_class: type) -> str:
    """Get the component type string for a component class."""
    return f"{component_class.__module__}.{component_class.__name__}"


def regenerate_test_data():
    """Regenerate all test data files."""
    print("Regenerating YAML test data files...")  # noqa: T201

    for test_case in TEST_COMPONENTS:
        component_class = test_case["component_class"]
        test_data_dir_name = test_case["test_data_dir"]
        component_name = test_case["name"]

        print(f"Processing {component_name}...")  # noqa: T201

        # Get component information
        component_type_str = get_component_type_str(component_class)
        component_schema = get_component_schema(component_class)

        # Generate YAML content
        schema_yaml = generate_defs_yaml_schema(component_type_str, component_schema)
        example_yaml = generate_defs_yaml_example_values(component_type_str, component_schema)

        # Ensure test data directory exists
        test_dir = TEST_DATA_DIR / test_data_dir_name
        test_dir.mkdir(parents=True, exist_ok=True)

        # Write schema file
        schema_file = test_dir / "expected_schema"
        schema_file.write_text(schema_yaml)
        print(f"  Updated {schema_file}")  # noqa: T201

        # Write example file
        example_file = test_dir / "expected_example"
        example_file.write_text(example_yaml)
        print(f"  Updated {example_file}")  # noqa: T201

    print("Done!")  # noqa: T201


if __name__ == "__main__":
    regenerate_test_data()
