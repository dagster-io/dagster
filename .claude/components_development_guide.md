# Dagster Components Development Guide

## Development Workflow for Components System

This guide provides practical workflows and patterns for developing features and fixing bugs in the Dagster components system.

## Understanding the Codebase

### Key Mental Models

#### 1. Three-Phase Processing Pipeline
```
YAML Files → ComponentDecl → Component Instance → Dagster Definitions
     ↓             ↓              ↓                    ↓
  Discovery    Parsing      Instantiation        Execution
```

#### 2. Context Flow
```
Environment → ComponentDeclLoadContext → ComponentLoadContext → Template Variables
     ↓                    ↓                       ↓                      ↓
File System         YAML Processing        Component Loading      Variable Resolution
```

#### 3. Inheritance Hierarchies
```
Component (ABC)
├── Resolvable (Mixin) - YAML template processing
└── Model (Pydantic) - Data validation

ComponentDeclLoadContext (Base)
└── ComponentLoadContext (Extended)
```

### Code Organization Patterns

#### Separation of Concerns
- **`core/`**: Framework logic (loading, resolution, context)
- **`component/`**: Component base classes and utilities  
- **`resolved/`**: Interfaces and mixins
- **`definitions.py`**: Integration with Dagster's definition system

#### Naming Conventions
- **`*_decl.py`**: YAML representation objects
- **`*_context.py`**: Context and environment objects
- **`*_module.py`**: Module loading and discovery
- **`template_vars.py`**: Template variable system

## Development Patterns

### Adding New Features

#### 1. Identify the Layer
```python
# YAML Layer - extend ComponentFileModel
class ComponentFileModel(BaseModel):
    new_field: Optional[str] = None  # Add new YAML field

# Component Layer - extend Component interface  
class Component(ABC):
    def new_method(self) -> Any: ...  # Add new component capability

# Context Layer - extend context classes
@dataclass(frozen=True)
class ComponentLoadContext(ComponentDeclLoadContext):
    new_context_info: Optional[str] = None  # Add context information
```

#### 2. Follow the Pipeline
```python
# Step 1: YAML parsing
def parse_yaml_extension(yaml_data: dict) -> ComponentFileModel:
    # Handle new YAML fields
    
# Step 2: Context creation
def create_extended_context(...) -> ComponentLoadContext:
    # Include new context information
    
# Step 3: Component processing
def process_component_extension(component: Component, context: ComponentLoadContext):
    # Use new feature in component loading
```

#### 3. Maintain Backward Compatibility
```python
# Wrong - breaks existing code
def existing_function(old_param, new_required_param): ...

# Right - preserves compatibility
def existing_function(old_param, new_optional_param=None): ...

# Right - create new function
def existing_function_extended(old_param, new_param): ...
```

### Bug Fixing Workflow

#### 1. Reproduce the Issue
```python
# Create minimal test case
def test_reproduce_bug():
    # Set up scenario that triggers the bug
    yaml_content = """
    type: buggy.Component
    attributes:
      problematic_field: "value"
    """
    
    # Attempt to reproduce
    with pytest.raises(ExpectedError):
        load_component_from_yaml(yaml_content)
```

#### 2. Identify the Layer
- **YAML parsing errors**: Check `defs_module.py`, `decl.py`
- **Template variable errors**: Check `template_vars.py`, context resolution
- **Component loading errors**: Check `component.py`, loading pipeline
- **Definition generation errors**: Check component `build_defs()` methods

#### 3. Trace the Pipeline
```python
# Add debug logging at each stage
logger.debug(f"YAML parsed: {file_model}")
logger.debug(f"Context created: {context.rendering_scope}")
logger.debug(f"Component loaded: {component}")
logger.debug(f"Definitions generated: {definitions}")
```

#### 4. Fix at the Right Level
```python
# Framework-level fix - affects all components
def context_with_injected_scope(...):
    # Fix template variable resolution

# Component-level fix - affects specific component type
class MyComponent(Component):
    def build_defs(self, context):
        # Fix definition generation
        
# YAML-level fix - update schema validation
class ComponentFileModel(BaseModel):
    field: str = Field(..., validation_alias="correct_field_name")
```

## Common Development Scenarios

### Scenario 1: Adding Template Variable Functionality

#### Problem Analysis
- Need to support new template variable source
- Must maintain backward compatibility
- Should follow existing patterns

#### Implementation Strategy
```python
# 1. Identify integration point
def context_with_injected_scope(context, component_cls, template_vars_module):
    # This is where template variables are merged

# 2. Create new template variable source
def get_new_template_vars_source(cls: type, context: ComponentDeclLoadContext) -> dict[str, Any]:
    # Extract template variables from new source
    
# 3. Integrate into pipeline
def context_with_injected_scope(context, component_cls, template_vars_module):
    existing_scope = get_existing_template_vars(component_cls)
    new_scope = get_new_template_vars_source(component_cls, context)
    merged_scope = {**existing_scope, **new_scope}  # New takes precedence
    return context.with_rendering_scope(merged_scope)
```

### Scenario 2: Adding YAML Configuration Options

#### Problem Analysis
- Need new YAML field
- Must validate configuration
- Should integrate with existing pipeline

#### Implementation Strategy
```python
# 1. Extend YAML model
class ComponentFileModel(BaseModel):
    existing_field: str
    new_configuration: NewConfigModel = Field(default_factory=NewConfigModel)

# 2. Process new configuration
def process_component_with_new_config(file_model: ComponentFileModel, context: ComponentLoadContext):
    if file_model.new_configuration:
        # Process the new configuration
        enhanced_context = enhance_context_with_config(context, file_model.new_configuration)
        return enhanced_context
    return context

# 3. Integrate into loading pipeline
def load_component_from_yaml(...):
    file_model = ComponentFileModel.model_validate(yaml_data)
    context = create_context(...)
    enhanced_context = process_component_with_new_config(file_model, context)
    component = load_component(file_model, enhanced_context)
```

### Scenario 3: Extending Component Capabilities

#### Problem Analysis
- Components need new interface method
- Must be optional for backward compatibility
- Should provide default implementation

#### Implementation Strategy
```python
# 1. Add optional method to base class
class Component(ABC):
    def new_capability(self, context: ComponentLoadContext) -> Optional[Any]:
        """Optional new capability - default implementation."""
        return None  # Safe default

# 2. Update loading pipeline to use new capability
def load_component_with_new_capability(component: Component, context: ComponentLoadContext):
    definitions = component.build_defs(context)
    
    # Use new capability if available
    if hasattr(component, 'new_capability') and callable(getattr(component, 'new_capability')):
        enhancement = component.new_capability(context)
        if enhancement:
            definitions = enhance_definitions(definitions, enhancement)
    
    return definitions

# 3. Components can opt into new capability
class ModernComponent(Component, Resolvable, Model):
    def new_capability(self, context: ComponentLoadContext) -> Enhancement:
        return Enhancement(...)  # Provide implementation
```

## Testing Strategies

### Unit Testing Patterns

#### Testing Framework Functions
```python
def test_framework_function():
    # Test with minimal, controlled inputs
    mock_context = create_mock_context(path="test/path")
    mock_component_cls = create_mock_component_class()
    
    result = framework_function(mock_context, mock_component_cls)
    
    assert result.expected_property == "expected_value"
```

#### Testing Component Integration
```python
def test_component_integration():
    # Use test utilities for realistic scenarios
    class TestComponent(Component, Resolvable, Model):
        test_field: str
        
        def build_defs(self, context):
            return Definitions(assets=[...])
    
    load_context, component = load_context_and_component_for_test(
        TestComponent, 
        {"test_field": "test_value"}
    )
    
    definitions = component.build_defs(load_context)
    assert len(definitions.assets) == 1
```

### Integration Testing Patterns

#### End-to-End YAML Loading
```python
def test_yaml_loading_end_to_end(tmp_path):
    # Create temporary YAML file
    yaml_file = tmp_path / "test.component.yaml"
    yaml_file.write_text("""
    type: test_project.TestComponent
    attributes:
      field: "{{ template_var }}"
    template_vars_module: .test_template_vars
    """)
    
    # Create template vars module
    template_vars_file = tmp_path / "test_template_vars.py"
    template_vars_file.write_text("""
    import dagster as dg
    
    @dg.template_var
    def template_var() -> str:
        return "resolved_value"
    """)
    
    # Test loading
    context = ComponentDeclLoadContext(path=yaml_file, defs_path=tmp_path)
    component = load_component_from_yaml(yaml_file, context)
    
    assert component.field == "resolved_value"
```

### Error Testing Patterns

#### Testing Error Conditions
```python
def test_error_handling():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        problematic_operation()
    
    # Verify error message contains helpful context
    assert "component type" in str(exc_info.value)
    assert "path/to/component.yaml" in str(exc_info.value)
```

#### Testing Edge Cases
```python
@pytest.mark.parametrize("edge_case", [
    {},  # Empty configuration
    {"invalid_field": "value"},  # Invalid field
    {"required_field": None},  # None for required field
])
def test_edge_cases(edge_case):
    with pytest.raises((ValidationError, DagsterInvalidDefinitionError)):
        ComponentFileModel.model_validate(edge_case)
```

## Debugging Techniques

### Logging Strategy
```python
import logging

logger = logging.getLogger(__name__)

def debug_component_loading(component_type: str, context: ComponentLoadContext):
    logger.debug(f"Loading component {component_type}")
    logger.debug(f"Context path: {context.path}")
    logger.debug(f"Rendering scope keys: {list(context.rendering_scope.keys())}")
    
    # Add breakpoint for interactive debugging
    if os.getenv("DEBUG_COMPONENTS"):
        import pdb; pdb.set_trace()
```

### Inspection Utilities
```python
def inspect_component_state(component: Component, context: ComponentLoadContext):
    """Debug utility to inspect component and context state."""
    print(f"Component type: {type(component)}")
    print(f"Component fields: {component.__dict__ if hasattr(component, '__dict__') else 'N/A'}")
    print(f"Context path: {context.path}")
    print(f"Context rendering scope: {context.rendering_scope}")
    
    # Check template variables
    if hasattr(component.__class__, 'get_additional_scope'):
        scope = component.__class__.get_additional_scope()
        print(f"Additional scope: {scope}")
```

### Common Debugging Scenarios

#### Template Variable Resolution Issues
```python
def debug_template_vars(component_cls: type, context: ComponentDeclLoadContext):
    # Check static template vars
    static_vars = get_static_template_vars(component_cls)
    print(f"Static template vars: {static_vars}")
    
    # Check context-aware template vars
    context_vars = get_context_aware_static_template_vars(component_cls, context)
    print(f"Context-aware template vars: {context_vars}")
    
    # Check additional scope
    additional_scope = component_cls.get_additional_scope()
    print(f"Additional scope: {additional_scope}")
```

#### Component Loading Issues
```python
def debug_component_loading(yaml_file_path: Path):
    # Check YAML parsing
    with open(yaml_file_path) as f:
        yaml_content = yaml.safe_load(f)
    print(f"YAML content: {yaml_content}")
    
    # Check file model validation
    file_model = ComponentFileModel.model_validate(yaml_content)
    print(f"File model: {file_model}")
    
    # Check component type resolution
    try:
        component_cls = resolve_component_type(file_model.type)
        print(f"Component class: {component_cls}")
    except Exception as e:
        print(f"Component resolution error: {e}")
```

## Performance Optimization

### Lazy Loading Patterns
```python
class LazyComponent(Component):
    def __init__(self, config):
        self._config = config
        self._cached_definitions = None
    
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        if self._cached_definitions is None:
            self._cached_definitions = self._compute_definitions(context)
        return self._cached_definitions
```

### Caching Strategies
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_template_vars(component_type: str) -> dict[str, Any]:
    """Cache template variables by component type."""
    component_cls = resolve_component_type(component_type)
    return get_static_template_vars(component_cls)
```

### Memory Management
```python
class MemoryEfficientComponent(Component):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        # Use generators for large datasets
        assets = (create_asset(item) for item in self.get_large_dataset())
        return Definitions(assets=list(assets))
    
    def get_large_dataset(self):
        # Yield items instead of creating large lists
        for item in data_source:
            yield process_item(item)
```

## Code Review Guidelines

### What to Look For

#### Backward Compatibility
- Are existing method signatures preserved?
- Are new parameters optional with sensible defaults?
- Are deprecation warnings added for changed behavior?

#### Error Handling
- Are errors informative and actionable?
- Is relevant context included in error messages?
- Are appropriate exception types used?

#### Type Safety
- Are type hints provided for public APIs?
- Are TYPE_CHECKING imports used correctly?
- Are generics used appropriately for extensibility?

#### Testing
- Are both unit and integration tests provided?
- Are edge cases covered?
- Are error conditions tested?

### Common Issues to Catch

#### Template Variable Problems
```python
# Wrong - optional context breaks type safety
def template_var_func(context=None): ...

# Right - explicit parameter requirements
def template_var_func(): ...  # No context
def template_var_func(context: ComponentLoadContext): ...  # Requires context
```

#### Context Type Confusion
```python
# Wrong - using specific type in framework code
def framework_func(context: ComponentLoadContext): ...  

# Right - using base type in framework code
def framework_func(context: ComponentDeclLoadContext): ...
```

#### Breaking Changes
```python
# Wrong - changing existing signature
def existing_function(old_param, new_required_param): ...

# Right - preserving compatibility
def existing_function(old_param, new_optional_param=None): ...
```

This development guide provides the practical knowledge and patterns needed to effectively work on any aspect of the Dagster components system.