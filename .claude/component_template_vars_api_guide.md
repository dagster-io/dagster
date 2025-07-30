# Component Template Variables API Reference

## Quick Reference

### Function Signatures
```python
# Core decorator
@template_var  # or @template_var()
def my_template_var(context: ComponentLoadContext) -> Any: ...

# Static template variables (Component class methods)
class MyComponent(Component):
    @staticmethod
    @template_var
    def no_context_var() -> str: ...
    
    @staticmethod
    @template_var
    def context_var(context: ComponentLoadContext) -> str: ...

# Framework functions
def get_static_template_vars(cls: type) -> dict[str, TemplateVarFn]
def get_context_aware_static_template_vars(cls: type, context: ComponentDeclLoadContext) -> dict[str, TemplateVarFn]
def invoke_inline_template_var(context: ComponentDeclLoadContext, tv: Callable) -> Any
```

### Parameter Rules
- **0 parameters**: No context, called as `func()`
- **1 parameter**: Context required, called as `func(context)`
- **>1 parameters**: Error - not supported

## API Functions

### `template_var` decorator
```python
@template_var
def my_var(context: ComponentLoadContext) -> str:
    return f"value_from_{context.path.name}"

@template_var()  # Also valid
def my_other_var() -> str:
    return "static_value"
```

**Purpose**: Mark functions as template variables for component YAML resolution

**Implementation details**:
- Sets `__dagster_template_var = True` attribute
- Preserves function metadata (name, docstring, etc.)
- Works with both module-level functions and static methods

### `get_static_template_vars(cls: type)`
```python
# Example usage
scope = get_static_template_vars(MyComponent)
# Returns: {'no_context_var': 'computed_value'}
```

**Purpose**: Extract static template variables that don't require context

**Behavior**:
- Only processes static methods with 0 parameters
- Invokes functions immediately and returns their values
- Skips functions that require context (1 parameter)
- Used by `Component.get_additional_scope()` for backward compatibility

**Returns**: Dictionary mapping variable names to their computed values

### `get_context_aware_static_template_vars(cls: type, context: ComponentDeclLoadContext)`
```python
# Example usage  
scope = get_context_aware_static_template_vars(MyComponent, load_context)
# Returns: {'context_var': 'computed_value_with_context'}
```

**Purpose**: Extract static template variables that require context

**Behavior**:
- Only processes static methods with 1 parameter
- Invokes functions with provided context
- Skips functions that don't need context (0 parameters)
- Used by framework code in `context_with_injected_scope`

**Returns**: Dictionary mapping variable names to their computed values

### `invoke_inline_template_var(context: ComponentDeclLoadContext, tv: Callable)`
```python
# Framework usage pattern
result = invoke_inline_template_var(context, my_template_function)
```

**Purpose**: Invoke template variable function with context if needed

**Behavior**:
- Inspects function signature to determine parameter count
- 0 params: calls `tv()`
- 1 param: calls `tv(context)`
- >1 params: raises `ValueError`

**Used by**: Module-level template variable resolution

## Context Types

### `ComponentDeclLoadContext`
- **When to use**: Framework code, low-level APIs
- **Properties**: `path`, `defs_path`, etc.
- **Usage**: Base context type for component loading

### `ComponentLoadContext` 
- **When to use**: User-facing APIs, component implementations
- **Properties**: Inherits from `ComponentDeclLoadContext` + additional features
- **Usage**: Most template variable functions should use this type

### Type Usage Pattern
```python
# Framework code - use base type
def framework_function(context: ComponentDeclLoadContext): ...

# User-facing API - use specific type  
@template_var
def user_template_var(context: ComponentLoadContext) -> str: ...
```

## Component Integration Points

### `Component.get_additional_scope()`
```python
class MyComponent(Component):
    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        # Default implementation
        return get_static_template_vars(cls)
        
    # Custom override (legacy compatibility)
    @classmethod  
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            'custom_var': 'custom_value',
            'helper_func': lambda: 'computed_result'
        }
```

**Critical**: This method may be overridden in legacy code and must remain signature-compatible.

### Framework Integration (`context_with_injected_scope`)
```python
def context_with_injected_scope(context, component_cls, template_vars_module):
    # Merge static template variables
    legacy_scope = component_cls.get_additional_scope()  # 0-param static methods + custom overrides
    context_aware_scope = get_context_aware_static_template_vars(component_cls, context)  # 1-param static methods
    merged_scope = {**legacy_scope, **context_aware_scope}  # Context-aware takes precedence
    
    context = context.with_rendering_scope(merged_scope)
    
    # Add module-level template variables if specified
    if template_vars_module:
        module_scope = load_and_invoke_module_template_vars(template_vars_module, context)
        context = context.with_rendering_scope(module_scope)
```

## Error Handling

### Common Errors

#### `"Static template var {name} must have 0 or 1 parameters"`
```python
# Wrong
@staticmethod
@template_var
def bad_template_var(context, extra_param):  # Too many parameters
    return "value"

# Right  
@staticmethod
@template_var
def good_template_var(context: ComponentLoadContext):  # Exactly 1 parameter
    return "value"
```

#### `"Template var must have 0 or 1 parameters"`
```python
# Module-level functions follow same rule
@template_var
def bad_module_var(context, extra_param):  # Error
    return "value"
```

### Validation Points

1. **Parameter count check**: Both static methods and module functions
2. **Context availability**: Context-requiring functions called without context
3. **Static method detection**: Ensuring `@staticmethod` decorator is present

## Testing Patterns

### Basic Test Structure
```python
def test_static_template_vars():
    class TestComponent(dg.Component, dg.Resolvable, dg.Model):
        @staticmethod
        @dg.template_var
        def no_context_var() -> str:
            return "no_context_value"
            
        @staticmethod
        @dg.template_var
        def context_var(context: ComponentLoadContext) -> str:
            return f"context_value_{context.path.name}"
    
    # Test no-context extraction
    scope = get_static_template_vars(TestComponent)
    assert scope == {'no_context_var': 'no_context_value'}
    
    # Test context-aware extraction
    load_context = create_test_context()
    context_scope = get_context_aware_static_template_vars(TestComponent, load_context)
    assert 'context_var' in context_scope
```

### Integration Test Pattern
```python
def test_component_integration():
    load_context, component = load_context_and_component_for_test(
        TestComponent, 
        {'field': '{{ no_context_var }}_{{ context_var }}'}
    )
    
    assert component.field == "no_context_value_context_value_dagster"
```

### Backward Compatibility Test
```python
def test_legacy_override():
    class LegacyComponent(Component):
        @classmethod
        def get_additional_scope(cls):
            return {'legacy_var': 'legacy_value'}
            
        @staticmethod
        @template_var
        def context_var(context):
            return 'context_value'
    
    # Test that both legacy and new work together
    load_context, component = load_context_and_component_for_test(
        LegacyComponent,
        {'field': '{{ legacy_var }}_{{ context_var }}'}
    )
    
    assert component.field == "legacy_value_context_value"
```

## Implementation Checklist

When adding template variable functionality:

- [ ] Add `@template_var` decorator to function
- [ ] Use 0 or 1 parameters only
- [ ] For static methods: add `@staticmethod` decorator first
- [ ] Import context type in `TYPE_CHECKING` block if needed
- [ ] Test both parameter patterns (0 and 1 param)
- [ ] Test integration with YAML component loading
- [ ] Verify backward compatibility if modifying framework code
- [ ] Add appropriate error handling for invalid parameter counts
- [ ] Document expected return types and behavior

This API reference would have provided clear examples and patterns for implementing the context-passing functionality correctly the first time.