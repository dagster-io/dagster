#!/usr/bin/env python3
"""Generic script to regenerate JSON schema and expected YAML output for component test data."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click


def run_command(cmd: list[str], cwd: Optional[str] = None) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running command {' '.join(cmd)}: {e}", err=True)
        click.echo(f"Stderr: {e.stderr}", err=True)
        sys.exit(1)


@click.command()
@click.argument("component_name")
@click.argument("test_dir_name", required=False)
def main(component_name: str, test_dir_name: Optional[str] = None):
    """Regenerate JSON schema and expected YAML output for a Dagster component.

    COMPONENT_NAME: Full component name (e.g., dagster_dbt.DbtProjectComponent)
    TEST_DIR_NAME: Test directory name (defaults to component name conversion)

    Examples:
        python regenerate_schema.py dagster_dbt.DbtProjectComponent

        python regenerate_schema.py dagster.DefsFolderComponent defs_folder_component
    """
    # Determine test directory name
    if not test_dir_name:
        # Convert component name to test directory format
        # e.g., dagster_dbt.DbtProjectComponent -> dbt_project_component
        component_parts = component_name.split(".")
        if len(component_parts) == 2:
            module, class_name = component_parts
            # Convert from CamelCase to snake_case
            import re

            snake_case = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
            snake_case = re.sub("([a-z0-9])([A-Z])", r"\1_\2", snake_case).lower()
            # Remove module prefix and "component" suffix if present
            if module.startswith("dagster_"):
                module_part = module[8:]  # Remove "dagster_"
                if snake_case.startswith(module_part):
                    snake_case = snake_case[len(module_part) :].lstrip("_")
            if snake_case.endswith("_component"):
                snake_case = snake_case[:-10]  # Remove "_component"
            test_dir_name = snake_case
        else:
            # Simple conversion for single part names
            test_dir_name = component_name.lower().replace(".", "_")

    # Set up paths
    script_dir = Path(__file__).parent
    test_dir = script_dir / test_dir_name
    repo_root = script_dir / "../../../../../.."

    # Create test directory if it doesn't exist
    test_dir.mkdir(exist_ok=True)

    click.echo(f"Regenerating schema for {component_name}...")
    click.echo(f"Test directory: {test_dir}")
    click.echo(f"Using command: dg utils inspect-component {component_name} --component-schema")

    # Generate the schema
    schema_output = run_command(
        ["dg", "utils", "inspect-component", component_name, "--component-schema"],
        cwd=str(repo_root.resolve()),
    )

    # Write schema to file
    schema_file = test_dir / "schema.json"
    with open(schema_file, "w") as f:
        f.write(schema_output)

    click.echo(f"Schema file generated at: {schema_file}")

    # Generate the expected YAML template output
    click.echo("Generating expected YAML template output...")

    # Import here to ensure we're in the right context
    sys.path.insert(0, str((script_dir / "../../..").resolve()))
    from dagster_dg_core.yaml_template.converter import YamlTemplate

    # Load and process schema
    schema = json.loads(schema_output)
    template = YamlTemplate.from_json_schema(schema)

    # Write expected output
    expected_output_file = test_dir / "expected_output.yaml"
    with open(expected_output_file, "w") as f:
        f.write(template.to_string())

    click.echo(f"Expected output file generated at: {expected_output_file}")

    # Create README.md file
    readme_file = test_dir / "README.md"
    component_display_name = component_name.split(".")[-1]
    readme_content = f"""# {component_display_name} Test Data

This directory contains test data for validating the YAML template conversion of the {component_name} JSON schema.

## Files

- **`schema.json`**: The JSON schema for the {component_display_name}, extracted using the `dg` CLI command
- **`expected_output.yaml`**: The expected YAML template output when processing the schema through the converter
- **`README.md`**: This documentation file

## Usage

### Regenerating the Schema and Expected Output

To regenerate both the schema and expected output, run from the test_data directory:

```bash
python ../regenerate_schema.py {component_name}
```

This will:
1. Use `dg utils inspect-component {component_name} --component-schema` to extract the JSON schema
2. Process the schema through the YAML template converter
3. Update both `schema.json` and `expected_output.yaml`

## Test Purpose

This test validates that the YAML template converter can handle the {component_name} schema, ensuring proper handling of:

- Complex nested structures
- Schema references (`$ref`) 
- Multiple type unions (`anyOf`)
- Various constraint types
- Arrays and objects

The test ensures the converter generates useful YAML templates for LLM consumption.
"""

    with open(readme_file, "w") as f:
        f.write(readme_content)

    click.echo(f"README file generated at: {readme_file}")
    click.echo("Done!")


if __name__ == "__main__":
    main()
