# Migrate NamedTuple to @record

Convert the specified NamedTuple class to use `@record` from `dagster_shared.record`.

## Use `@record` (simple case)

When `__new__` only contains `check.*_param` calls with no coercion:

```python
@record
class Foo:
    x: str
    y: Optional[int] = None
```

## Use `@record_custom` when:

1. **Any custom logic** - validation, invariants, conditionals
2. **Collection coercion** - `check.opt_*_param` coerces `None` → empty collection

Coercion functions requiring `@record_custom`:

- `check.opt_mapping_param` / `check.opt_dict_param` → `{}`
- `check.opt_list_param` / `check.opt_sequence_param` → `[]`
- `check.opt_set_param` → `set()`

Callers may pass `None` explicitly even without a default - preserve the coercion:

```python
@record_custom
class Foo(IHaveNew):
    tags: Mapping[str, str]

    def __new__(cls, tags: Optional[Mapping[str, str]] = None):
        return super().__new__(cls, tags={} if tags is None else tags)
```

When using `@record_custom`, there should be no defaults set on the field definitions, only the `__new__` arguments.

## Conversion steps

1. Remove `NamedTuple` inheritance and inline field definitions
2. Add `@record` or `@record_custom` decorator
3. Move fields to class body with type annotations
4. Delete `check.*_param` calls (auto-generated) unless coercion needed
5. Keep only custom validation in `__new__` for `record_custom`
6. Handle NamedTuple method usage - search codebase for calls to `._replace(`, `._asdict(`, `._fields` on this class:
   - **Option A**: Update callsites to use `@record` equivalents (from `dagster_shared.record`):
     - `obj._replace(...)` → `copy(obj, ...)` or `replace(obj, ...)`
     - `obj._asdict()` → `as_dict(obj)`
     - `Cls._fields` → `get_record_annotations(Cls).keys()`
   - **Option B**: Add `LegacyNamedTupleMixin` to preserve NamedTuple API compatibility
7. Use kwargs only in `super().__new__()` for `record_custom`
8. Run `make ruff`

## Positional args

For public APIs needing positional arg support: `@record(kw_only=False)`
