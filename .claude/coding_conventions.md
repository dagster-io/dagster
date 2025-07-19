# Coding Conventions

## Type Annotations

- Type hints required for all Python code
- Use builtin `dict` and `set` instead of `typing.Dict`, `typing.Set`

## Immutable Objects

- Use `@record` from `dagster_shared.record` for lightweight, immutable objects, or whereever you would use NamedTuple.
