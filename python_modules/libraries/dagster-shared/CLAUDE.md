# Dagster Shared Library - AI Development Guide

**Note: This file is machine-optimized for AI/LLM consumption and analysis.**

## Overview

The `dagster_shared` library provides foundational utilities and patterns used across the entire Dagster codebase. This includes data structures, validation utilities, serialization, and common patterns that maintain consistency across all Dagster packages.

## @record Usage and Best Practices

### Using @record from dagster_shared.record

The `@record` decorator is a core utility in the Dagster codebase that provides immutable, functional-style data structures. It is used instead of standard `@dataclass` throughout the codebase for better performance and immutability guarantees.

**Import Pattern:**
```python
from dagster_shared.record import record

@record
class MyDataModel:
    field1: str
    field2: int
    metadata: dict[str, Any]
```

### Creating New Instances (Immutable Updates)

**CRITICAL**: The `@record` decorator does **NOT** provide a `.replace()` method like `@dataclass`. This is a common source of confusion and type errors.

**❌ WRONG - replace() method does not exist:**
```python
@record
class Plan:
    title: str
    metadata: dict[str, Any]

# This will cause a pyright/mypy type error
updated_plan = current_plan.replace(metadata=new_metadata)
```

**✅ CORRECT - Create new instance explicitly:**
```python
@record  
class Plan:
    title: str
    metadata: dict[str, Any]

# Create new instance with updated fields
updated_plan = Plan(
    title=current_plan.title,
    metadata={
        **current_plan.metadata,
        "new_field": "new_value",
    },
)
```

### Common Patterns

**Updating nested dictionaries:**
```python
updated_plan = Plan(
    title=current_plan.title,
    summary=current_plan.summary,
    steps=current_plan.steps,
    metadata={
        **current_plan.metadata,  # Keep existing metadata
        "refinement_method": "claude_refinement",
        "user_feedback": feedback,
    },
)
```

**Updating lists:**
```python
updated_plan = Plan(
    title=current_plan.title,
    steps=[*current_plan.steps, new_step],  # Add new step
    metadata=current_plan.metadata,
)
```

**Conditional updates:**
```python
updated_metadata = current_plan.metadata
if some_condition:
    updated_metadata = {**updated_metadata, "extra_field": "value"}

updated_plan = Plan(
    title=current_plan.title,
    metadata=updated_metadata,
)
```

**Updating single fields:**
```python
# When only updating one field, still create a new instance
updated_plan = Plan(
    title="New Title",  # Updated field
    summary=current_plan.summary,
    steps=current_plan.steps,
    risks=current_plan.risks,
    prerequisites=current_plan.prerequisites,
    success_criteria=current_plan.success_criteria,
    metadata=current_plan.metadata,
)
```

### Type Safety and Immutability

- **All `@record` classes are immutable by design**
- Fields cannot be modified after creation
- PyRight/mypy will catch attempts to use non-existent `.replace()` method
- Always create new instances rather than trying to mutate existing ones
- This pattern follows the functional programming bias of the Dagster codebase

### Performance Benefits

The `@record` decorator provides several performance benefits over standard `@dataclass`:

- More efficient memory usage through structural sharing
- Faster instance creation for immutable data
- Better garbage collection characteristics
- Optimized hash computation for use in sets and dict keys

### Debugging Common Errors

**Error**: `Cannot access attribute "replace" for class "MyRecord"`

**Solution**: Use explicit instance creation instead:
```python
# Instead of this:
new_obj = old_obj.replace(field=new_value)

# Do this:
new_obj = MyRecord(
    field=new_value,
    other_field=old_obj.other_field,
    # ... all other fields
)
```

**Error**: Attempting to modify fields directly

**Solution**: Remember that `@record` instances are immutable:
```python
# Instead of this:
obj.field = new_value  # Will raise AttributeError

# Do this:
obj = MyRecord(
    field=new_value,
    other_field=obj.other_field,
)
```

## Why @record Instead of @dataclass?

The Dagster codebase uses `@record` instead of `@dataclass` for several reasons:

1. **Immutability by Default**: Prevents accidental mutation of data structures
2. **Functional Programming Style**: Aligns with Dagster's functional programming bias
3. **Performance**: Better memory usage and performance characteristics
4. **Consistency**: Uniform pattern across the entire codebase
5. **Type Safety**: Better integration with static type checking

## Integration with Other Dagster Patterns

The `@record` decorator works seamlessly with other Dagster patterns:

- **Serialization**: Records can be serialized/deserialized automatically
- **Configuration**: Used in configuration objects throughout Dagster
- **Event Handling**: Core event types use `@record` for consistency
- **API Boundaries**: Used in API request/response objects

This documentation ensures that developers working with Dagster understand the proper patterns for immutable data structures and avoid common pitfalls when working with `@record` classes.