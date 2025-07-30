# Dagster Components System Architecture

## System Overview

The Dagster Components system provides a declarative way to define and compose Dagster assets, jobs, and other definitions using YAML files and Python Component classes. This system bridges YAML configuration with Python implementation.

## Core Concepts

### Components vs Definitions
- **Component**: A reusable Python class that can generate Dagster definitions
- **Definition**: The actual Dagster objects (Assets, Jobs, etc.) that execute
- **Component Instance**: A specific configuration of a Component (usually from YAML)

### Key Design Principles
1. **Declarative Configuration**: YAML files describe what you want, not how to build it
2. **Reusable Components**: Python classes that can be instantiated with different configurations
3. **Type Safety**: Pydantic models for validation and type checking
4. **Context Awareness**: Components have access to their loading environment
5. **Composition**: Components can contain other components (tree structure)

## Architecture Layers

### 1. YAML Layer (`*.component.yaml` files)
```yaml
type: my_project.MyComponent
attributes:
  table_name: "users"
  database_url: "postgresql://..."
template_vars_module: .template_vars
```

**Purpose**: Declarative configuration of component instances
**Location**: Usually in `defs/` directories
**Processing**: Parsed into `ComponentFileModel` objects

### 2. Component Classes (Python)
```python
class MyComponent(dg.Component, dg.Resolvable, dg.Model):
    table_name: str
    database_url: str
    
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions(assets=[create_table_asset(self.table_name)])
```

**Purpose**: Reusable logic for generating Dagster definitions
**Key Methods**:
- `build_defs()`: Generate actual Dagster definitions
- `get_additional_scope()`: Provide template variables
- `load()`: Custom loading logic (optional)

### 3. Context System
```python
ComponentDeclLoadContext  # Base context for loading
└── ComponentLoadContext   # Extended context for component instances
```

**Purpose**: Provide environment information during loading
**Contains**: File paths, environment variables, parent context, etc.

### 4. Resolution System
**Purpose**: Convert YAML + Component classes into Dagster definitions
**Process**: YAML → ComponentDecl → Component Instance → Definitions

## Key File Structure

```
dagster/components/
├── component/
│   ├── component.py          # Base Component class
│   ├── template_vars.py      # Template variable system
│   └── component_scaffolder.py
├── core/
│   ├── context.py           # Context classes
│   ├── decl.py             # ComponentDecl (YAML representation)
│   ├── defs_module.py      # Module loading and resolution
│   └── tree.py             # Component tree structure
├── resolved/
│   ├── base.py             # Resolvable interface
│   ├── model.py            # Model base class
│   └── context.py          # Resolution context
└── definitions.py          # LazyDefinitions wrapper
```

## Component Loading Pipeline

### 1. Discovery Phase
```python
# Find all *.component.yaml files in defs/ directories
component_files = discover_component_files(defs_path)
```

### 2. YAML Parsing Phase
```python
# Parse YAML into ComponentFileModel
file_model = ComponentFileModel.model_validate(yaml_content)
# Contains: type, attributes, template_vars_module, requirements, etc.
```

### 3. ComponentDecl Creation
```python
# Create declaration object
decl = ComponentDecl(
    component_type=file_model.type,
    component_file_model=file_model,
    path=component_path
)
```

### 4. Context Creation
```python
# Create loading context with environment info
context = ComponentDeclLoadContext(
    path=component_path,
    defs_path=defs_root,
    # ... other context info
)
```

### 5. Template Variable Resolution
```python
# Inject template variables into context
context = context_with_injected_scope(
    context=context,
    component_cls=component_class,
    template_vars_module=file_model.template_vars_module
)
```

### 6. Component Instantiation
```python
# Load component class and instantiate
component_cls = load_component_class(decl.component_type)
component = component_cls.load(file_model.attributes, context)
```

### 7. Definition Generation
```python
# Generate Dagster definitions
definitions = component.build_defs(context)
```

## Template Variable System

### Three Sources of Template Variables

1. **Static Methods on Component Classes**:
```python
class MyComponent(Component):
    @staticmethod
    @template_var
    def get_prefix(context: ComponentLoadContext) -> str:
        return f"prod_{context.path.name}"
```

2. **Module-level Functions**:
```python
# In template_vars.py module
@template_var
def get_database_url(context: ComponentLoadContext) -> str:
    return os.getenv("DATABASE_URL")
```

3. **Custom get_additional_scope() Overrides**:
```python
class CustomComponent(Component):
    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {"custom_helper": lambda x: f"processed_{x}"}
```

### Resolution Order
1. Component static template variables (0-param and 1-param)
2. Module-level template variables (if `template_vars_module` specified)
3. Later scopes take precedence over earlier ones

### Jinja2 Integration
Template variables are made available in YAML as Jinja2 variables:
```yaml
attributes:
  table_name: "{{ get_prefix }}_users_{{ env('ENVIRONMENT') }}"
```

## Component Base Classes

### `Component` (Abstract Base)
```python
class Component(ABC):
    @abstractmethod
    def build_defs(self, context: ComponentLoadContext) -> Definitions: ...
    
    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]: ...
    
    @classmethod
    def load(cls, attributes: Optional[BaseModel], context: ComponentLoadContext) -> Self: ...
```

### `Resolvable` (Mixin)
- Enables YAML attribute resolution with Jinja2 templates
- Processes `{{ template_var }}` expressions in YAML attributes

### `Model` (Pydantic Wrapper)
- Provides Pydantic BaseModel functionality with Dagster defaults
- Handles type validation and serialization

### Common Inheritance Pattern
```python
class MyComponent(Component, Resolvable, Model):
    # Pydantic fields for configuration
    table_name: str
    schema_name: str = "public"
    
    # Implementation
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        # Generate Dagster definitions
        pass
```

## Context System Deep Dive

### `ComponentDeclLoadContext`
**When Created**: During YAML file processing
**Contains**: 
- `path`: Path to component file
- `defs_path`: Root defs directory
- `environment`: Environment variables
- `rendering_scope`: Template variables

**Methods**:
- `with_rendering_scope(scope)`: Add template variables
- `defs_relative_module_name(path)`: Convert path to module name

### `ComponentLoadContext`
**Extends**: `ComponentDeclLoadContext`
**When Created**: When instantiating specific components
**Additional Features**: Component-specific context information

### Context Usage Patterns
```python
# Framework code - use base type
def framework_function(context: ComponentDeclLoadContext): ...

# Component implementation - use specific type
def build_defs(self, context: ComponentLoadContext) -> Definitions: ...

# Template variables - accept context parameter
@template_var
def my_template_var(context: ComponentLoadContext) -> str: ...
```

## Error Handling Patterns

### Common Error Types
1. **Component Discovery Errors**: Missing files, invalid YAML
2. **Template Resolution Errors**: Undefined variables, syntax errors
3. **Component Loading Errors**: Import failures, missing classes
4. **Validation Errors**: Invalid attributes, type mismatches
5. **Definition Building Errors**: Runtime errors in `build_defs()`

### Error Context
Errors include rich context information:
- Component file path
- Line numbers (for YAML errors)
- Component type and attributes
- Template variable context

### Error Handling Best Practices
```python
try:
    component = load_component(decl, context)
except Exception as e:
    raise DagsterInvalidDefinitionError(
        f"Failed to load component {decl.component_type} from {decl.path}: {e}"
    ) from e
```

## Extension Points

### Adding New Component Types
1. Create Component class inheriting from `Component, Resolvable, Model`
2. Implement `build_defs()` method
3. Add to module where it can be discovered
4. Register in `pyproject.toml` if needed

### Adding Template Variable Sources
1. Static methods: Add `@staticmethod @template_var` to Component class
2. Module-level: Create module with `@template_var` functions
3. Custom scope: Override `get_additional_scope()` class method

### Extending Context Information
1. Subclass `ComponentLoadContext` with additional fields
2. Update context creation in loading pipeline
3. Ensure backward compatibility with existing components

## Testing Strategies

### Unit Testing Components
```python
def test_my_component():
    context = create_test_context()
    component = MyComponent(table_name="test_table")
    definitions = component.build_defs(context)
    
    assert len(definitions.assets) == 1
    assert definitions.assets[0].key.to_user_string() == "test_table"
```

### Integration Testing with YAML
```python
def test_component_loading():
    yaml_content = """
    type: my_project.MyComponent
    attributes:
      table_name: "test_table"
    """
    
    load_context, component = load_context_and_component_for_test(
        MyComponent, {"table_name": "test_table"}
    )
    
    definitions = component.build_defs(load_context)
    # Test generated definitions
```

### Testing Template Variables
```python
def test_template_variables():
    class TestComponent(Component, Resolvable, Model):
        field: str
        
        @staticmethod
        @template_var
        def test_var() -> str:
            return "test_value"
    
    load_context, component = load_context_and_component_for_test(
        TestComponent, {"field": "{{ test_var }}"}
    )
    
    assert component.field == "test_value"
```

## Performance Considerations

### Component Loading
- Components are loaded lazily when accessed
- Template variables are resolved once during loading
- Caching is used for module imports and component class loading

### Memory Usage
- Component instances are kept in memory after loading
- Large components should implement lazy loading patterns
- Consider using `LazyDefinitions` for expensive definitions

### Optimization Opportunities
- Template variable caching
- Component class registration
- Parallel component loading
- Incremental reloading

## Debugging Guide

### Common Issues and Solutions

#### "Component type not found"
- Check import paths in `type` field
- Verify component class is in discoverable module
- Check `pyproject.toml` registry configuration

#### "Template variable undefined"
- Check `@template_var` decorator is applied
- Verify `template_vars_module` path is correct
- Check template variable parameter count (0 or 1 only)

#### "Validation error"
- Check Pydantic field types match YAML values
- Verify required fields are provided
- Check for typos in attribute names

#### "Context errors"
- Ensure context type matches function signature
- Check TYPE_CHECKING imports for context types
- Verify context is available where needed

### Debug Tools
```python
# Check component discovery
from dagster.components.core.defs_module import discover_component_files
files = discover_component_files(defs_path)

# Test template variable resolution
from dagster.components.component.template_vars import get_static_template_vars
scope = get_static_template_vars(MyComponent)

# Inspect component loading
from dagster.components.core.decl import ComponentDecl
decl = ComponentDecl.from_yaml_file(component_yaml_path)
```

## Best Practices

### Component Design
- Keep components focused on single responsibilities
- Use composition over inheritance
- Provide sensible defaults
- Make components testable in isolation

### YAML Organization
- Group related components in directories
- Use consistent naming conventions
- Document component schemas
- Provide example configurations

### Template Variables
- Keep template variable functions pure (no side effects)
- Use descriptive names
- Provide type hints
- Document expected return types

### Error Handling
- Provide actionable error messages
- Include relevant context in errors
- Use appropriate exception types
- Handle edge cases gracefully

This architecture guide provides the foundational understanding needed to work effectively with any aspect of the Dagster components system.