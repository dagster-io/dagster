# `dg` Cheatsheet

## Overview

The `dg` CLI is Dagster's modern command-line interface that provides a streamlined, component-based approach to building data pipelines. It offers automatic definition discovery, integrated Python environment management with `uv`, and a declarative component framework.

## Core dg Commands

### Project Management

```bash
# Run the Dagster webserver/daemon to interact with assets in the UI
dg dev

# Serve local Dagster documentation
dg docs serve

# Check validity of definitions
dg check defs

# Check YAML configuration validity
dg check yaml
```

### Asset Operations

```bash
# List asset definitions
dg list defs

# List available components
dg list components

# List environment variables used by components
dg list env

# Materialize an asset from the CLI
dg launch --assets <asset_key>
```

### Component Scaffolding
```bash
# Scaffold a new component definition
dg scaffold defs <component-type> <component-path>

# Scaffold with Python format (instead of YAML)
dg scaffold defs <component-type> <component-path> --format python

# Scaffold an inline component
dg scaffold defs inline-component --typename ComponentName component_name

# Scaffold a custom component
dg scaffold component
```

### Environment Variables (Dagster+)
```bash
# Push environment variables to deployment
dg plus create env

# Pull environment variables locally
dg plus pull env
```

## Component Framework

### Component Definition Structure (YAML)
```yaml
type: <component-type>
attributes:
  key1: value1
  key2: value2

# Optional: Post-processing to modify assets
post_processing:
  assets:
    - target: "*"  # Target all assets or specific ones
      attributes:
        group_name: "my_group"
        kinds:
          - "some_kind"
        tags:
          environment: production
```

### Multiple Components in One File
```yaml
# First component
type: component_type_1
attributes:
  param1: value1
---
# Second component
type: component_type_2
attributes:
  param2: value2
```

## Template Variables and UDFs

### Template Variables Module
Create a `template_vars.py` file:
```python
import dagster as dg

@dg.template_vardef
def table_prefix() -> str:
    return "staging" if not os.getenv("IS_PROD") else "warehouse"

@dg.template_vardef
def get_database_url(context: dg.ComponentContext) -> str:
    # Context-aware template variable
    env = context.deployment_type
    return f"postgresql://host/{env}_db"
```

Reference in YAML:
```yaml
type: SomeComponent
attributes:
  table_name: "{{ table_prefix }}_orders"
  connection_string: "{{ get_database_url }}"
```

### Template UDFs
For complex logic in configurations:
```python
def generate_tags() -> Callable[[str, bool], dict[str, str]]:
    def _generate_tags(classification: str, has_pii: bool = False) -> dict[str, str]:
        return {
            "data_classification": classification,
            "pii_contains": str(has_pii).lower(),
        }
    return _generate_tags
```

## Partitions

### Adding Partitions via YAML
```yaml
type: SomeComponent
attributes:
  # Component attributes

post_processing:
  assets:
    - target: "*"
      attributes:
        partitions_def: "{{ daily_partitions }}"
```

### Adding Partitions via Python
```python
@dg.component_instance
class PartitionedComponent(BaseComponent):
    def get_spec(self) -> dg.AssetSpec:
        return super().get_spec().replace_attributes(
            partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01")
        )
```

## Environment Variables

### Using Environment Variables in Components
```yaml
type: SomeComponent
attributes:
  database:
    host: "{{ env.DB_HOST }}"
    password: "{{ env.DB_PASSWORD }}"

# Declare required environment variables
requirements:
  env:
    - DB_HOST
    - DB_PASSWORD
```

### Local Development with .env
Create a `.env` file in your project root:
```
DB_HOST=localhost
DB_PASSWORD=secret
```

## Creating Custom Components

### Basic Component Structure
```python
import dagster as dg
from typing import Sequence

class MyCustomComponent(dg.Component, dg.Model, dg.Resolvable):
    # Component parameters (from YAML attributes)
    asset_key: list[str]
    script_path: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(key=self.asset_key)
        def my_asset(context):
            # Asset implementation
            pass

        return dg.Definitions(assets=[my_asset])

    def get_spec(self) -> dg.AssetSpec:
        # Optional: Add metadata
        return dg.AssetSpec(
            key=self.asset_key,
            metadata={"script_path": self.script_path}
        )
```

### Component with Custom Scaffolding
```python
@scaffold_with(custom_scaffolder)
class MyComponent(dg.Component):
    def build_defs(self, context):
        # Component implementation
        pass

def custom_scaffolder(path: Path, params: dict):
    # Create custom files during scaffolding
    (path / "template.sh").write_text("#!/bin/bash\n# Generated script")
```

### Subclassing Existing Components
```python
class CustomDbtComponent(dg.DbtProjectComponent):
    def execute(self, context, **kwargs):
        # Add custom execution logic
        context.log.info("Running custom DBT execution")
        return super().execute(context, **kwargs)

    @classmethod
    def get_additional_scope(cls):
        # Add custom template variables
        return {
            "custom_tag": lambda x: f"dbt_{x}",
        }
```

## Testing Components

### Testing Pattern
```python
from dagster import dg
from pathlib import Path

def test_component():
    # Create test sandbox
    with dg.create_defs_folder_sandbox() as sandbox:
        # Scaffold component
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            attributes={"asset_key": ["test_asset"]}
        )

        # Load and test component
        with sandbox.load_component_and_build_defs(defs_path) as (component, defs):
            # Verify component properties
            assert len(component.assets) == 1
            assert component.asset_key == ["test_asset"]

            # Test materialization
            result = dg.materialize(defs.get_assets_def("test_asset"))
            assert result.success

def load_project_component(component_path):
    """Helper for testing existing components"""
    project_root = Path(__file__).parent.parent
    tree = dg.ComponentTree.for_project(project_root)
    component = tree.load_component_at_path(component_path)
    defs = tree.build_defs_at_path(component_path)
    return component, defs
```

## Post-Processing

### Modifying Assets After Creation
```yaml
type: SomeComponent
attributes:
  # Component config

post_processing:
  assets:
    # Apply to all assets
    - attributes:
        kinds:
          - "python"
        tags:
          team: "data-eng"

    # Apply to specific assets
    - target: "orders_*"  # Use asset selection syntax
      attributes:
        group_name: "orders"
        owners:
          - "team:orders@company.com"

    # Complex targeting
    - target: "tag:critical=true"
      attributes:
        auto_materialize_policy:
          policy_type: eager
```

## Common Component Types

### DBT Component
```yaml
type: dagster_dbt.DbtProjectComponent
attributes:
  workspace:
    project_path: dbt/my_project

post_processing:
  assets:
    - target: "*"
      attributes:
        group_name: "dbt_models"
```

### Sling Replication Component
```yaml
type: dagster_sling.SlingReplicationCollectionComponent
attributes:
  connections:
    SOURCE_DB:
      type: postgres
      host: "{{ env.SOURCE_HOST }}"
  replications:
    - source: SOURCE_DB
      target: TARGET_DB
      streams:
        - "public.orders"
```

### Shell Command Component
```yaml
type: ShellCommandComponent
attributes:
  script_path: scripts/etl.sh
  asset_specs:
    - key: ["processed_data"]
      description: "Data processed by shell script"
```

## Best Practices

1. **Component Organization**
   - Use registered components for reusable logic
   - Use inline components for project-specific, one-off patterns
   - Group related components in subdirectories

2. **Environment Configuration**
   - Always declare required environment variables in `requirements.env`
   - Use `.env` files for local development
   - Configure different values for dev/staging/prod in Dagster+

3. **Template Variables**
   - Use template variables for configuration that changes between environments
   - Use template UDFs for complex configuration logic
   - Keep template logic testable and maintainable

4. **Testing**
   - Test component scaffolding, instantiation, and execution
   - Use sandbox utilities for isolated testing
   - Verify asset keys and metadata generation

5. **Post-Processing**
   - Use post-processing to add consistent metadata across assets
   - Apply organization-wide standards (tags, owners, groups)
   - Avoid modifying core component logic when post-processing suffices
