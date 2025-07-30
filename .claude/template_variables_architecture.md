# Template Variables Architecture Guide

## Overview

Template variables in Dagster components provide dynamic value injection into YAML component definitions. There are two main types:

1. **Module-level template variables**: Defined in separate Python modules
2. **Static method template variables**: Defined as `@staticmethod` on Component classes

## Architecture Components

### Core Functions

#### `template_var` decorator (`template_vars.py:22-32`)
- **Purpose**: Marks functions as template variables
- **Usage**: `@template_var` or `@template_var()`
- **Implementation**: Sets `__dagster_template_var` attribute to `True`
- **Critical**: Works with both module-level functions and static methods

#### `get_static_template_vars(cls: type) -> dict[str, TemplateVarFn]`
- **Purpose**: Extracts static template variables that don't require context
- **Scope**: Only processes static methods with 0 parameters
- **Used by**: `Component.get_additional_scope()` for backward compatibility
- **Key behavior**: Skips context-requiring functions

#### `get_context_aware_static_template_vars(cls: type, context: ComponentDeclLoadContext)`
- **Purpose**: Extracts static template variables that require context
- **Scope**: Only processes static methods with 1 parameter (context)
- **Used by**: Framework code in `context_with_injected_scope`
- **Key behavior**: Invokes functions with provided context

### Context Types Hierarchy

```
ComponentDeclLoadContext (base)
└── ComponentLoadContext (extends ComponentDeclLoadContext)
```

**Critical**: Use `ComponentDeclLoadContext` for typing in framework code since that's what `context_with_injected_scope` receives.

### Template Resolution Pipeline

1. **Component scope resolution** (`defs_module.py:441-458`):
   ```python
   def context_with_injected_scope(context, component_cls, template_vars_module):
       # Step 1: Get legacy static template vars (0 params)
       legacy_scope = component_cls.get_additional_scope()
       
       # Step 2: Get context-aware static template vars (1 param)
       context_aware_scope = get_context_aware_static_template_vars(component_cls, context)
       
       # Step 3: Merge (context-aware takes precedence)
       merged_scope = {**legacy_scope, **context_aware_scope}
       
       # Step 4: Add to rendering context
       context = context.with_rendering_scope(merged_scope)
   ```

2. **Module-level template variables** (if `template_vars_module` specified):
   ```python
   # Load module and find template vars
   template_var_fns = find_inline_template_vars_in_module(module)
   
   # Invoke with context using same pattern as static methods
   scope = {
       name: invoke_inline_template_var(context, tv)
       for name, tv in template_var_fns.items()
   }
   ```

### Parameter Pattern for Template Variables

Both module-level and static method template variables follow the same pattern:

```python
def invoke_inline_template_var(context: ComponentDeclLoadContext, tv: Callable) -> Any:
    sig = inspect.signature(tv)
    if len(sig.parameters) == 1:
        return tv(context)  # Pass context
    elif len(sig.parameters) == 0:
        return tv()  # No context needed
    else:
        raise ValueError(f"Template var must have 0 or 1 parameters, got {len(sig.parameters)}")
```

## Backward Compatibility Constraints

### `Component.get_additional_scope()` is Sacred
- **Cannot be changed**: Legacy code may override this method
- **Must remain signature-compatible**: `@classmethod def get_additional_scope(cls) -> Mapping[str, Any]`
- **Framework solution**: Create separate functions and merge results at framework level

### Legacy Override Example
```python
class LegacyComponent(Component):
    @classmethod
    def get_additional_scope(cls):
        # Custom logic that must continue working
        return {'custom_var': 'custom_value', 'helper_func': lambda: 'result'}
```

## Implementation Patterns

### Adding Context Support to Static Methods

**Wrong approach** (breaks compatibility):
```python
def get_additional_scope(cls, context=None):  # NEVER DO THIS
```

**Right approach** (separation of concerns):
```python
# Keep legacy function unchanged
def get_static_template_vars(cls: type) -> dict[str, TemplateVarFn]:
    # Only 0-parameter static methods

# Create new function for context-aware
def get_context_aware_static_template_vars(cls: type, context: ComponentDeclLoadContext):
    # Only 1-parameter static methods

# Merge at framework level
def context_with_injected_scope(...):
    legacy_scope = component_cls.get_additional_scope()
    context_aware_scope = get_context_aware_static_template_vars(component_cls, context)
    merged_scope = {**legacy_scope, **context_aware_scope}
```

### Type Safety Best Practices

1. **Use proper context types**:
   ```python
   # Framework code - use base type
   def framework_func(context: ComponentDeclLoadContext): ...
   
   # User-facing APIs - use specific type
   def user_func(context: ComponentLoadContext): ...
   ```

2. **Import in TYPE_CHECKING blocks**:
   ```python
   from typing import TYPE_CHECKING
   
   if TYPE_CHECKING:
       from dagster.components.core.context import ComponentDeclLoadContext
   
   def my_func(context: "ComponentDeclLoadContext"): ...
   ```

## Testing Considerations

### Test Both Paths
Always test both legacy and new functionality:

```python
def test_backward_compatibility():
    # Test that get_additional_scope overrides still work
    
def test_new_functionality():
    # Test context-aware static template variables

def test_mixed_scenarios():
    # Test components with both types of template variables
```

### Common Test Patterns

```python
class TestComponent(dg.Component, dg.Resolvable, dg.Model):
    @staticmethod
    @dg.template_var
    def no_context_var() -> str:
        return "no_context_value"

    @staticmethod
    @dg.template_var
    def context_var(context: ComponentLoadContext) -> str:
        return f"context_value_{context.path.name}"
```

## Common Pitfalls

1. **Signature inspection confusion**: Always use `inspect.signature(func).parameters` to check parameter count
2. **Context type mismatches**: Framework uses `ComponentDeclLoadContext`, users see `ComponentLoadContext`
3. **Import cycles**: Use `TYPE_CHECKING` imports for context types in `template_vars.py`
4. **Breaking compatibility**: Never modify existing public method signatures
5. **Double processing**: Ensure static template vars aren't processed twice (once in legacy, once in context-aware)

## Performance Notes

- Template variable resolution happens at component load time, not runtime
- Static template variables are cached as their return values in the rendering scope
- Context is passed by reference, no performance overhead
- Module-level template variables are loaded once per module

## Debugging Guide

### Common Issues

1. **"Template var requires context but none provided"**:
   - Static method has 1 parameter but is being called via legacy path
   - Check that framework code is using `get_context_aware_static_template_vars`

2. **Type errors with context**:
   - Check context type hierarchy: `ComponentLoadContext` extends `ComponentDeclLoadContext`
   - Use base type (`ComponentDeclLoadContext`) in framework code

3. **Template variable not found**:
   - Check `@template_var` decorator is applied
   - Verify method is static: `@staticmethod @template_var`
   - Check parameter count (0 or 1 only)

### Debug Functions

```python
# Check if function is template var
from dagster.components.component.template_vars import is_template_var
print(is_template_var(my_function))

# Check if method is static
from dagster.components.component.template_vars import is_staticmethod
print(is_staticmethod(MyComponent, MyComponent.my_method))

# Inspect parameter count
import inspect
print(len(inspect.signature(my_function).parameters))
```

This architecture documentation would have saved significant time by clearly outlining the constraints, patterns, and implementation approach needed for this task.