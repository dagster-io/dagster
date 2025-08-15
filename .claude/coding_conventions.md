# Coding Conventions

## Overall Guidance and Style

- In the Dagster repository we bias towards functional-style programming with lightweight immutable objects.
  Instead of modifying objects, we copy them and replace specific attributes (e.g. with `replace` in `dagster_shared.record`). "Result"
  objects should be @record-annotated classes.
- You do not need to create imports into `__init__.py` files unless 1) explicitly asked or 2) if this is a public API annotated with @public. For internal classes and functions we rely on absolute imports.
- Do not use `print` in production code. For CLI output, use `click.echo()` for proper output handling and testing compatibility.

## Python Version Requirements

- **Target Python Version**: Python 3.9 and above (maintaining compatibility with older versions)
- **Modern Python Features**: Use Python 3.9+ features where appropriate
- **Type Annotations**: Use built-in generic types (e.g., `list[str]`, `dict[str, Any]`) - available in Python 3.9+

## Type Annotations

- Type hints required for all Python code
- **ALWAYS use builtin types for annotations**: `dict`, `list`, `set`, `tuple` instead of `typing.Dict`, `typing.List`, `typing.Set`, `typing.Tuple`
- **NEVER import or use** `typing.Dict`, `typing.List`, `typing.Set`, `typing.Tuple` - use built-in types instead (available in Python 3.9+)
- **Union Types**: **MUST use `Union[X, Y]`** from typing module (Python 3.9 compatibility) - **NEVER use `X | Y` syntax**
- **Optional Types**: **MUST use `Optional[X]`** from typing module (Python 3.9 compatibility) - **NEVER use `X | None` syntax**
- **CRITICAL**: The `X | Y` and `X | None` union syntax requires Python 3.10+ and is **FORBIDDEN** in this codebase
- All Python code must pass `pyright` type checking with zero errors

## Import Organization

- **ALWAYS use top-level (module-scoped) imports** - avoid function-scoped imports except in specific cases
- **Acceptable exceptions for function-scoped imports:**
  1. **TYPE_CHECKING blocks**: Imports only needed for type annotations
  2. **Circular import resolution**: When imports would create circular dependencies
  3. **Optional dependencies**: When import failure should be handled gracefully
  4. **Expensive lazy loading**: When imports are computationally expensive and conditionally used
  5. **Performance-critical lazy imports**: For modules that significantly slow down CLI startup time

- **Examples of correct import patterns:**

```python
# ✅ GOOD: Top-level imports
from contextlib import contextmanager
from dagster._core.definitions import JobDefinition
from dagster._utils.error import DagsterError

@contextmanager
def my_function():
    job = JobDefinition(...)
    # Use imports directly
```

```python
# ❌ BAD: Function-scoped imports without justification
@contextmanager
def my_function():
    from dagster._core.definitions import JobDefinition
    from dagster._utils.error import DagsterError
    job = JobDefinition(...)
```

```python
# ✅ ACCEPTABLE: TYPE_CHECKING imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster import JobDefinition
    from dagster._core.storage.dagster_run import DagsterRun
```

```python
# ✅ ACCEPTABLE: Avoiding circular imports
def create_job():
    # Import here to avoid circular dependency
    from dagster._core.definitions import JobDefinition
    return JobDefinition(...)
```

```python
# ✅ ACCEPTABLE: Performance-critical lazy imports for slow libraries
@click.command()
def deploy_command():
    # Lazy import to avoid slowing CLI startup
    from dagster_cloud_cli.commands.ci import deploy_impl
    from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition
    # ... use imports
```

### Performance-Critical Libraries

The following libraries are known to significantly slow down import time and **MUST be lazy-loaded** using function-scoped imports when used in CLI commands:

- `jinja2` - Template engine with heavy initialization
- `requests` - HTTP library with certificate loading
- `dagster_cloud_cli.*` - Cloud CLI modules with complex dependencies
- `urllib.request` - Built-in HTTP client with TLS setup
- `yaml` - YAML parsing with C extensions
- `typer` - CLI framework with rich dependencies
- `pydantic` - Data validation with compiled validators

**Example of correct lazy import pattern:**

```python
# ✅ GOOD: Lazy import of performance-critical libraries
@click.command()
def my_command():
    """Command that uses expensive libraries."""
    # Lazy import to avoid loading at CLI startup
    import yaml
    import requests
    from dagster_cloud_cli.commands.ci import deploy_impl

    # Use the imports in function body
    config = yaml.safe_load(config_file)
    response = requests.get(api_url)
```

## Data Structures

- **ALWAYS use `@record` for dataclasses, lightweight objects, and immutable objects in Dagster codebase except in specific circumstances**
  - **Import**: `from dagster_shared.record import record `
  - **DEFAULT CHOICE**: When creating any new class that holds data, use `@record` unless you have a specific reason not to
  - Use `@record` for:
    - Data transfer objects (DTOs) and result objects
    - Configuration objects
    - Error/mismatch reporting objects
    - Analysis results and comparison objects
    - Any immutable data structure
    - Lightweight objects that hold related data
    - Classes that represent findings, issues, or validation results
  - ONLY use `@dataclass` when:
    - Mutability is required
    - Working with external libraries that expect dataclasses

### Naming Conventions for @record Methods

- **Use `with_*` naming for methods that return new instances with additional data**
  - ✅ `result.with_error("message")` - Returns new ValidationResult with added error
  - ✅ `result.with_warning("message")` - Returns new ValidationResult with added warning
  - ✅ `result.with_parsing_failed()` - Returns new ValidationResult with failed parsing state
  - ❌ `result.add_error("message")` - Confusing, sounds like it mutates the object
  - ❌ `result.append_warning("message")` - Implies mutation rather than returning new instance
- **Rationale**: The `with_*` convention makes it clear that:
  1. The method returns a new instance (immutable pattern)
  2. The original object is not modified
  3. The new instance includes the specified addition/change

## Context Managers

**DO NOT assign unentered context manager objects to intermediate variables** - use them directly as the target of `with`:

```python
# BAD: Assigning context manager to variable before entering
run_context = build_run_status_sensor_context(
    sensor_name="test_sensor",
    dagster_run=dagster_run,
)
with run_context:
    # work with run_context

# GOOD: Use context manager directly in with statement
with build_run_status_sensor_context(
    sensor_name="test_sensor",
    dagster_run=dagster_run,
) as run_context:
    # work with run_context
```

**Rationale**: Assigning an unentered context manager to a variable can lead to resource leaks if the variable is accidentally used outside the context manager, and makes the code less clear about when resources are acquired and released.

**Exception**: When you need to access properties of the context manager object after it exits (e.g., results set during `__exit__`), it's acceptable to assign to a variable:

```python
# ACCEPTABLE: When you need post-exit access to context manager properties
run_context = build_run_status_sensor_context(sensor_name, dagster_run)
with run_context:
    # do work within context
    pass
# Access properties set during __exit__
return SomeResult(run_id=run_context.run_id)
```

## Exception Handling Guidelines

This codebase follows specific norms for exception handling to maintain clean, predictable code:

### General Principles

- **By default, exceptions should NOT be used as control flow**
- **Do NOT implement "fallback" behavior in catch blocks** - exceptions should bubble up the stack to be handled at appropriate boundaries
- **Avoid catching broad `Exception` types** unless you have a specific reason

### Acceptable Uses of Exception Handling

1. **Error Boundaries**: Meaningful divisions in software that have sensible default error behavior
   - CLI commands (top-level exception handlers for user-friendly error messages)
   - Asset materialization operations (individual asset failures shouldn't fail entire job)
2. **API Compatibility**: Compensating for APIs that use exceptions for control flow
   - When third-party APIs use exceptions to indicate missing keys/values
   - When storage systems have different capabilities that can't be detected a priori
3. **Embellishing Exceptions**: Adding context to in-flight exceptions before re-raising

### Implementation Pattern: Encapsulation

When violating exception norms is necessary, **encapsulate the violation within a function**:

```python
# GOOD: Exception handling encapsulated in helper function
def _get_asset_value_with_fallback(context, asset_key, default_value):
    """
    Try to get asset value, fallback to default.

    Some storage systems may not support certain operations,
    so we use exception handling to detect this case.
    """
    try:
        return context.instance.get_latest_materialization_event(asset_key).asset_materialization.metadata
    except Exception:
        return default_value

# BAD: Exception control flow exposed in main logic
try:
    metadata = context.instance.get_latest_materialization_event(asset_key).asset_materialization.metadata
except Exception:
    metadata = default_value
```

### Preferred Approach: Proactive Checking

When possible, check conditions that cause errors before making calls:

```python
# PREFERRED: Check condition beforehand
if context.instance.has_asset_key(asset_key):
    return get_asset_metadata(asset_key)
else:
    return get_default_metadata()

# AVOID: Using exceptions to discover the condition
try:
    return get_asset_metadata(asset_key)  # Will fail if key doesn't exist
except KeyError:
    return get_default_metadata()
```

#### Dictionary/Mapping Access

**ALWAYS use membership testing (`in`) before accessing dictionary keys** instead of catching `KeyError`:

```python
# PREFERRED: Proactive key existence checking
if asset_key in asset_metadata:
    value = asset_metadata[asset_key]
    # process value
else:
    # handle missing key case
    handle_missing_asset()

# AVOID: Using KeyError as control flow
try:
    value = asset_metadata[asset_key]
    # process value
except KeyError:
    handle_missing_asset()
```

**Rationale**: Membership testing is more explicit about intent, performs better, and avoids using exceptions for control flow. The `in` operator clearly indicates that you're checking for key existence before access.

### Validation and Input Checking

**DO NOT catch exceptions just to re-raise them with different messages** unless you're adding meaningful context:

```python
# BAD: Unnecessary exception transformation
try:
    validate_asset_config(config)
except ValidationError as e:
    raise DagsterConfigError(f"Invalid asset config: {e}")

# GOOD: Let the original exception bubble up with its specific error details
validate_asset_config(config)

# ACCEPTABLE: Adding meaningful context before re-raising
try:
    validate_asset_config(config)
except ValidationError as e:
    raise DagsterConfigError(f"Asset '{asset_name}' has invalid configuration: {e}") from e
```

**Rationale**: The original exception often contains more precise error information than generic wrapper messages. Only transform exceptions when you're adding valuable context that helps with debugging or user experience.

### Exception Swallowing Anti-Patterns

**NEVER swallow exceptions silently** - always let them bubble up to appropriate error boundaries:

```python
# BAD: Silently swallowing exceptions
try:
    if not asset_exists(asset_key):
        return
    for partition in get_partitions(asset_key):
        if should_process_partition(partition):
            process_partition(partition)
except (AssetNotFoundError, PartitionError):
    return  # Silently fails, hiding real problems

# GOOD: Let exceptions bubble up
if not asset_exists(asset_key):
    return
for partition in get_partitions(asset_key):
    if should_process_partition(partition):
        process_partition(partition)
```

**NEVER implement fallback behavior in exception handlers** unless you're at an appropriate error boundary:

```python
# BAD: Using exceptions for fallback logic
try:
    return parse_asset_key_from_string(key_str)
except ValueError:
    # Fallback to manual parsing
    return AssetKey([key_str])

# GOOD: Let the original exception bubble up
return parse_asset_key_from_string(key_str)
```

**Rationale**: Exception swallowing masks real problems and makes debugging extremely difficult. If an exception occurs, it usually indicates a genuine issue that needs to be addressed, not hidden.

## CLI Development

- **ALWAYS use `click` for building CLI tools** - it's the standard CLI framework in Dagster
- **Use `click.echo()` instead of `print()`** for all CLI output
  - Ensures proper output handling in different environments
  - Works correctly with output redirection and testing
  - Handles Unicode properly across platforms
- **Example:**

```python
# ✅ GOOD: Using click.echo for CLI output
import click

@click.command()
def my_command():
    click.echo("Processing started...")
    click.echo(f"Found {count} items")

# ❌ BAD: Using print in CLI code
@click.command()
def my_command():
    print("Processing started...")  # Don't use print
    print(f"Found {count} items")
```

## Project Compatibility

- **Code must be compatible with Python 3.9 and later**
- **Use Python 3.9+ features** where appropriate (built-in generics like `list[str]`, `dict[str, Any]`, etc.)
- **CRITICAL**: The `|` union syntax (`X | Y`, `X | None`) requires Python 3.10+ and is **NOT SUPPORTED** - always use `Union[X, Y]` and `Optional[X]` from the typing module for Python 3.9 compatibility

## Documentation Style

- **Follow Google-style docstrings** for all public functions and classes
- Include Args, Returns, and Raises sections where applicable
- Add examples in docstrings for complex functionality

## Package Organization

- **NEVER use `__all__` in subpackage `__init__.py` files**
- **Only use `__all__` in top-level package `__init__.py` files** to define public APIs
- **For re-exporting symbols in `__init__.py` files**: Use the explicit import pattern `import foo as foo` instead of relying on `__all__`
  - This makes re-exports explicit and avoids the pitfalls of `__all__` management
  - Example: `from dagster.submodule import SomeClass as SomeClass`
- Rely on absolute imports for internal classes and functions
