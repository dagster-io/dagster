---
title: "Advanced config types"
description: Dagster's config system supports a variety of more advanced config types.
sidebar_position: 200
---

In some cases, you may want to define a more complex [config schema](run-configuration) for your assets and ops. For example, you may want to define a config schema that takes in a list of files or complex data. In this guide, we'll walk through some common patterns for defining more complex config schemas.

## Attaching metadata to config fields

Config fields can be annotated with metadata, which can be used to provide additional information about the field, using the Pydantic <PyObject section="config" module="dagster" object="Field"/> class.

For example, we can annotate a config field with a description, which will be displayed in the documentation for the config field. We can add a value range to a field, which will be validated when config is specified.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_metadata_config" endBefore="end_metadata_config" />

## Defaults and optional config fields

Config fields can have an attached default value. Fields with defaults are not required, meaning they do not need to be specified when constructing the config object.

For example, we can attach a default value of `"hello"` to the `greeting_phrase` field, and can construct `MyAssetConfig` without specifying a phrase. Fields which are marked as `Optional`, such as `person_name`, implicitly have a default value of `None`, but can also be explicitly set to `None` as in the example below.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_optional_config" endBefore="end_optional_config" />

### Required config fields

By default, fields which are typed as `Optional` are not required to be specified in the config, and have an implicit default value of `None`. If you want to require that a field be specified in the config, you may use an ellipsis (`...`) to [require that a value be passed](https://docs.pydantic.dev/usage/models/#required-fields).

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_required_config" endBefore="end_required_config" />

## Basic data structures

Basic Python data structures can be used in your config schemas along with nested versions of these data structures. The data structures which can be used are:

- `List`
- `Dict`
- `Mapping`

For example, we can define a config schema that takes in a list of user names and a mapping of user names to user scores.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_basic_data_structures_config" endBefore="end_basic_data_structures_config" />

## Nested schemas

Schemas can be nested in one another, or in basic Python data structures.

Here, we define a schema which contains a mapping of user names to complex user data objects.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_nested_schema_config" endBefore="end_nested_schema_config" />

## Permissive schemas

By default, `Config` schemas are strict, meaning that they will only accept fields that are explicitly defined in the schema. This can be cumbersome if you want to allow users to specify arbitrary fields in their config. For this purpose, you can use the `PermissiveConfig` base class, which allows arbitrary fields to be specified in the config.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_permissive_schema_config" endBefore="end_permissive_schema_config" />

## Union types

Union types are supported using Pydantic [discriminated unions](https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions). Each union type must be a subclass of <PyObject section="config" module="dagster" object="Config"/>. The `discriminator` argument to <PyObject section="config" module="dagster" object="Field"/> specifies the field that will be used to determine which union type to use. Discriminated unions provide comparable functionality to the `Selector` type in the legacy Dagster config APIs.

Here, we define a config schema which takes in a `pet` field, which can be either a `Cat` or a `Dog`, as indicated by the `pet_type` field.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_union_schema_config" endBefore="end_union_schema_config" />

### YAML and config dictionary representations of union types

The YAML or config dictionary representation of a discriminated union is structured slightly differently than the Python representation. In the YAML representation, the discriminator key is used as the key for the union type's dictionary. For example, a `Cat` object would be represented as:

```yaml
pet:
  cat:
    meows: 10
```

In the config dictionary representation, the same pattern is used:

```python
{
    "pet": {
        "cat": {
            "meows": 10,
        }
    }
}
```

## Enum types

Python enums which subclass `Enum` are supported as config fields. Here, we define a schema that takes in a list of users, whose roles are specified as enum values:

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_enum_schema_config" endBefore="end_enum_schema_config" />

### YAML and config dictionary representations of enum types

The YAML or config dictionary representation of a Python enum uses the enum's name. For example, a YAML specification of the user list above would be:

```yaml
users_list:
  Bob: GUEST
  Alice: ADMIN
```

In the config dictionary representation, the same pattern is used:

```python
{
    "users_list": {
        "Bob": "GUEST",
        "Alice": "ADMIN",
    }
}
```

## Validated config fields

Config fields can have custom validation logic applied using [Pydantic validators](https://docs.pydantic.dev/usage/validators/). Pydantic validators are defined as methods on the config class, and are decorated with the `@validator` decorator. These validators are triggered when the config class is instantiated. In the case of config defined at runtime, a failing validator will not prevent the launch button from being pressed, but will raise an exception and prevent run start.

Here, we define some validators on a configured user's name and username, which will throw exceptions if incorrect values are passed in the launchpad or from a schedule or sensor.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_validated_schema_config" endBefore="end_validated_schema_config" />
