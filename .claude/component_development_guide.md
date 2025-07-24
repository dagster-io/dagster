# Component Development Guide

This guide provides comprehensive guidance for developing Dagster component classes. It is designed for Claude Code to use when generating or writing new components, covering patterns from simple hardcoded components to complex integration components.

## Component Architecture Overview

Dagster components follow a clear inheritance hierarchy with specific patterns for different use cases:

### Core Component Hierarchy

```
Component (ABC)
├── ExecutableComponent (for asset execution)
│   ├── FunctionComponent (Python functions)
│   ├── PythonScriptComponent (subprocess execution)
│   ├── UvRunComponent (uv-managed subprocess)
│   └── SqlComponent (SQL execution)
│       └── TemplatedSqlComponent (templated SQL)
├── Integration Components (external services)
│   ├── FivetranAccountComponent
│   ├── SlingReplicationCollectionComponent
│   ├── DltLoadCollectionComponent
│   └── [other service integrations]
└── System Components (file/folder management)
    ├── CompositeYamlComponent
    └── DefsFolderComponent
```

### Key Mixins and Interfaces

- **`Resolvable`**: Enables schema-based configuration and template resolution
- **`Model`**: Pydantic-based schema definition (recommended over BaseModel)
- **`ABC`**: Abstract base class marker for components requiring implementation

## Component Naming Conventions

### Integration Components
For components that pull assets from external services:

- **Single Entity Pattern**: `[Service][Entity]Component`
  - `FivetranAccountComponent` - pulls all connectors from a Fivetran account
  - `PowerBIWorkspaceComponent` - pulls all assets from a PowerBI workspace
  - `AirbyteCloudWorkspaceComponent` - pulls all connections from Airbyte workspace

- **Collection Pattern**: `[Service][Action]CollectionComponent`
  - `SlingReplicationCollectionComponent` - manages multiple Sling replications
  - `DltLoadCollectionComponent` - manages multiple dlt loads
  - Used when objects are configured within the component rather than discovered

### Execution Components
- **Technology Pattern**: `[Technology][Artifact]Component`
  - `PythonScriptComponent` - executes Python scripts
  - `TemplatedSqlComponent` - executes templated SQL

**Naming Rule**: Component names should describe what objects/assets the component represents or manages.

## Basic Component Patterns

### Configurable Component

The standard pattern for configurable, reusable components:

```python
import dagster as dg
from typing import List

class DatabaseTableComponent(dg.Component, dg.Resolvable, dg.Model):
    """Component for creating assets from database tables.

    This component connects to a database and creates a Dagster asset
    for a specified table, with configurable column selection.

    Examples:
        Basic usage:

        ```yaml
        type: my_package.DatabaseTableComponent
        attributes:
          table_name: "users"
          columns: ["id", "name", "email"]
        ```

        With custom database URL:

        ```yaml
        type: my_package.DatabaseTableComponent
        attributes:
          table_name: "orders"
          columns: ["id", "customer_id", "amount"]
          database_url: "{{ env.DATABASE_URL }}"
        ```
    """

    table_name: str
    columns: List[str]
    database_url: str = "postgresql://localhost/mydb"

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        @dg.asset(key=self.table_name)
        def table_asset():
            # Use self.table_name, self.columns, etc.
            return execute_query(f"SELECT {', '.join(self.columns)} FROM {self.table_name}")

        return dg.Definitions(assets=[table_asset])
```

**Key Points:**
- Inherit from `Component + Resolvable + Model`
- Use `dg.Model` over `pydantic.BaseModel` for new components
- All configuration becomes available as `self.attributes`

## Executable Component Patterns

For components that execute code to materialize assets:

### Function-Based Execution

```python
from dagster.components.lib.executable_component.function_component import FunctionComponent
from dagster.components.resolved.core_models import ResolvedAssetSpec

class CustomFunctionComponent(FunctionComponent):
    """Component that executes a custom function."""

    # Inherits execution: Union[FunctionSpec, ResolvableCallable]
    # Inherits assets: Optional[list[ResolvedAssetSpec]]

    # Add component-specific configuration
    custom_param: str

    def invoke_execute_fn(self, context, component_load_context):
        # Custom execution logic if needed
        return super().invoke_execute_fn(context, component_load_context)
```

### SQL-Based Execution

```python
from dagster.components.lib.sql_component.sql_component import SqlComponent
from dagster.components.lib.sql_component.sql_client import SQLClient

class CustomSqlComponent(SqlComponent):
    """Component that executes custom SQL."""

    # Inherits connection: SQLClient
    # Add component-specific configuration
    table_name: str

    def get_sql_content(self, context) -> str:
        return f"CREATE TABLE {self.table_name} AS SELECT * FROM source_table"
```

## Integration Component Patterns

For components that integrate with external services. These follow consistent patterns for translation, resource management, and asset generation.

### Standard Integration Component Structure

```python
from collections.abc import Sequence
from functools import cached_property
from typing import Annotated, Callable, Optional, Union
import dagster as dg
from dagster.components.utils import TranslatorResolvingInfo

# 1. Translation Function Types
TranslationFn = Callable[[dg.AssetSpec, ExternalSystemProps], dg.AssetSpec]

def resolve_translation(context: dg.ResolutionContext, model):
    info = TranslatorResolvingInfo(
        "props",  # Variable name for external data
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )
    return lambda base_asset_spec, props: info.get_asset_spec(
        base_asset_spec,
        {
            "props": props,
            "spec": base_asset_spec,
        },
    )

ResolvedTranslationFn = Annotated[
    TranslationFn,
    dg.Resolver(
        resolve_translation,
        model_field_type=Union[str, dg.AssetAttributesModel],
    ),
]

# 2. Proxy Translator Class
class ProxyExternalSystemTranslator(BaseExternalSystemTranslator):
    def __init__(self, fn: TranslationFn):
        self.fn = fn

    def get_asset_spec(self, props: ExternalSystemProps) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(props)
        return self.fn(base_asset_spec, props)

# 3. Main Component Class
@dg.scaffold_with(CustomComponentScaffolder)
class ExternalSystemComponent(dg.Component, dg.Model, dg.Resolvable):
    """Integrates with ExternalSystem to create Dagster assets.

    This component connects to ExternalSystem and automatically discovers
    assets, creating corresponding Dagster assets for each discovered object.

    Examples:
        Basic usage with connection details:

        ```yaml
        type: my_package.ExternalSystemComponent
        attributes:
          workspace:
            api_key: "{{ env.EXTERNAL_API_KEY }}"
            endpoint: "https://api.external-system.com"
        ```

        With filtering and custom translation:

        ```yaml
        type: my_package.ExternalSystemComponent
        attributes:
          workspace:
            api_key: "{{ env.EXTERNAL_API_KEY }}"
          selector:
            by_name: ["important_dataset", "critical_table"]
          translation:
            key_prefix: "external_system"
            group_name: "external_data"
        ```
    """

    # Resource/connection configuration
    workspace: ExternalSystemWorkspace

    # Optional filtering
    selector: Optional[Callable[[ExternalSystemObject], bool]] = None

    # Optional translation
    translation: Optional[ResolvedTranslationFn] = None

    @cached_property
    def translator(self) -> BaseExternalSystemTranslator:
        if self.translation:
            return ProxyExternalSystemTranslator(self.translation)
        return BaseExternalSystemTranslator()

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Use external service's asset building function
        assets = build_external_system_assets(
            workspace=self.workspace,
            translator=self.translator,
            selector_fn=self.selector,
        )
        return dg.Definitions(assets=assets)
```

### Integration Component Checklist

When creating integration components:

1. **Translation Support**: Always include optional translation functions
2. **Resource Management**: Use existing Dagster resources if available, otherwise use connection objects directly
3. **Filtering/Selection**: Provide mechanisms to select subsets of external objects
4. **Consistent Naming**: Follow the naming patterns described above
5. **Proxy Translator**: Use proxy pattern to wrap translation functions
6. **Cached Properties**: Use `@cached_property` for expensive computations

## Resolver Pattern Usage

### When to Use Resolvers

**Use Resolvers for:**
- Complex object construction from configuration
- Loading external resources or connections
- Translation function configuration
- Function resolution from import paths
- Dynamic value resolution based on context

**Don't Use Resolvers for:**
- Simple primitive values (strings, numbers, booleans)
- Template string resolution (handled automatically by Resolvable)
- Static configuration that doesn't need transformation
- Direct field assignments

### Common Resolver Patterns

```python
# Resource resolution
workspace: Annotated[
    ExternalWorkspace,
    dg.Resolver(
        lambda context, model: ExternalWorkspace(
            **resolve_fields(model, ExternalWorkspace, context)
        )
    ),
]

# Function resolution from import path
execute_fn: Annotated[
    Callable,
    dg.Resolver(resolve_callable, model_field_type=str)
]

# Translation function resolution
translation: Annotated[
    TranslationFn,
    dg.Resolver(
        resolve_translation,
        model_field_type=Union[str, dg.AssetAttributesModel],
    ),
]
```

**Resolver Rule**: If you need external object loading, complex configuration transformation, or function resolution, use a resolver. Template strings are resolved automatically by the Resolvable system. For simple values, use direct field assignment.

## Custom Scaffolding

Components can provide custom scaffolding to enhance usability:

### Basic Scaffolder

```python
from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest
import textwrap

class CustomComponentScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest) -> None:
        # Create component directory
        component_dir = request.target_path
        component_dir.mkdir(parents=True, exist_ok=True)

        # Generate defs.yaml
        defs_file = component_dir / "defs.yaml"
        defs_file.write_text(
            textwrap.dedent(f'''
                type: {request.type_name}
                attributes:
                  param1: "example_value"
                  param2: 42
            ''').strip()
        )

        # Generate additional files if needed
        config_file = component_dir / "config.yaml"
        config_file.write_text("# Configuration file")

@dg.scaffold_with(CustomComponentScaffolder)
class CustomComponent(dg.Component, dg.Resolvable, dg.Model):
    # Component implementation
    pass
```

### Integration Component Scaffolding

Integration components should scaffold:
1. `defs.yaml` with proper configuration structure
2. Connection/credential configuration files
3. Example configuration files for the external system

## File Organization Standards

### Standard Component Structure

```
dagster_[service]/
├── components/
│   └── [component_name]/
│       ├── __init__.py
│       ├── component.py      # Main component class
│       └── scaffolder.py     # Custom scaffolder (optional)
└── [other service files...]
```

### Component File Template

```python
# Standard imports
from collections.abc import Sequence
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
from dagster.components.utils import TranslatorResolvingInfo
# Service-specific imports...

# Translation patterns (for integration components)
TranslationFn = Callable[...]
ResolvedTranslationFn = Annotated[...]

# Component class
@dg.scaffold_with(ComponentScaffolder)  # Optional
class ServiceComponent(dg.Component, dg.Model, dg.Resolvable):
    """Brief description of what this component does.

    Detailed explanation of the component's purpose, what external service
    it integrates with, and what assets it creates.

    Examples:
        Basic usage:

        ```yaml
        type: my_package.ServiceComponent
        attributes:
          param1: "value1"
          param2: 42
        ```

        Advanced usage with optional features:

        ```python
        component = ServiceComponent(
            param1="value1",
            param2=42,
            optional_feature=True
        )
        ```
    """

    # Configuration fields

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Implementation
        return dg.Definitions(...)
```

## Component Development Checklist

When developing any component:

### Required Elements
- [ ] Inherits from `Component`
- [ ] Implements `build_defs(self, context: ComponentLoadContext) -> Definitions`
- [ ] Includes comprehensive docstring
- [ ] Uses appropriate naming convention

### For Configurable Components
- [ ] Inherits from `Resolvable` and `Model`
- [ ] Uses `dg.Model` over `pydantic.BaseModel`
- [ ] Provides sensible defaults where appropriate
- [ ] Uses resolvers only when necessary

### For Integration Components
- [ ] Follows standard translation pattern
- [ ] Includes optional filtering/selection
- [ ] Uses `@cached_property` for expensive operations
- [ ] Manages resources appropriately
- [ ] Provides custom scaffolding

### For Executable Components
- [ ] Inherits from appropriate executable base class
- [ ] Implements required execution methods
- [ ] Handles resource dependencies properly
- [ ] Returns appropriate result types

### Testing Requirements
- [ ] Has comprehensive test coverage following [Component Testing Patterns](.claude/component_testing_patterns.md)
- [ ] Tests scaffolding behavior (if custom scaffolding provided)
- [ ] Tests component loading and asset generation
- [ ] Tests error handling for invalid configurations
- [ ] Tests translation functions (for integration components)
- [ ] Tests resource/connection handling

## Common Patterns and Utilities

### Asset Specification Patterns

```python
# Simple asset specs
assets = [dg.AssetSpec(key="my_asset")]

# Complex asset specs with translation
from dagster.components.resolved.core_models import ResolvedAssetSpec
assets: Optional[list[ResolvedAssetSpec]] = None
```

### Resource Management

**Choose the appropriate pattern based on existing code:**

```python
# Option 1: Use existing Dagster resource (preferred if available)
from dagster_service import ServiceResource

@cached_property
def service_resource(self) -> ServiceResource:
    return ServiceResource(
        api_key=self.api_key,
        endpoint=self.endpoint
    )

def build_defs(self, context):
    assets_with_resources = [
        asset.with_resources({"service": self.service_resource})
        for asset in base_assets
    ]
    return dg.Definitions(assets=assets_with_resources)

# Option 2: Direct connection object (for component-native integrations)
@cached_property
def connection(self) -> ServiceClient:
    return ServiceClient(
        api_key=self.api_key,
        endpoint=self.endpoint
    )

def build_defs(self, context):
    # Use connection directly in asset creation
    assets = build_service_assets(connection=self.connection)
    return dg.Definitions(assets=assets)
```

**Resource Decision Rule**: Use existing Dagster resources if they exist for the service. For new component-native integrations, connection objects are preferred over creating new resources.


## Testing Requirements

**All new component classes must have comprehensive tests.** Components should be testable using the patterns detailed in [Component Testing Patterns](.claude/component_testing_patterns.md).

### Required Test Coverage

Every component should include tests for:

1. **Scaffolding behavior** (if custom scaffolding is provided)
2. **Component loading and configuration parsing**
3. **Asset generation** with expected keys and metadata
4. **Error handling** for invalid configurations
5. **Translation functions** (for integration components)
6. **Resource/connection handling**

### Basic Test Example

```python
def test_my_component():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=MyComponent,
            component_body={
                "type": "my_package.MyComponent",
                "attributes": {"param": "value"}
            }
        )

        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
            assert isinstance(component, MyComponent)
            # Test component behavior
            expected_keys = {AssetKey("expected_asset")}
            assert defs.resolve_asset_graph().get_all_asset_keys() == expected_keys
```

**Testing Reference**: See [Component Testing Patterns](.claude/component_testing_patterns.md) for comprehensive testing guidance, including:
- Asset translation testing with `TestTranslation`
- Op customization testing with `TestOpCustomization`
- Environment and resource mocking patterns
- Multi-component integration testing
- Component execution and materialization testing
