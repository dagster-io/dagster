# Coding Conventions

## Overall Guidance and style

- In the Dagster repository we bias towards functional-style programming with lightweight immutable objects.
  Instead of modifying objects, we copy them and replace specific attributes (e.g. with `replace` in `dagster_shared.record`). "Result"
  objects should be @record-annotated classes.
- You do not need to create imports into `__init__.py` files unless 1) explicitly asked or 2) if this is a public API annotated with @public. For internal classes and functions we rely on absolute imports.

## Type Annotations

- Type hints required for all Python code
- **ALWAYS use builtin types for annotations**: `dict`, `list`, `set`, `tuple` instead of `typing.Dict`, `typing.List`, `typing.Set`, `typing.Tuple`
- **NEVER import or use** `typing.Dict`, `typing.List`, `typing.Set`, `typing.Tuple` - these are deprecated in Python 3.9+

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

## Other conventions

- Do not use `print` unless specifically requested. They are illegal in the code base unless mark with "# noqa: T201" on the same line.
