# 0.7.0 Migration Guide

The 0.7.0 release contains a number of breaking API changes. While listed
in the changelog, this document goes into more detail about how to
resolve the change easily. Most of the eliminated or changed APIs
can be adjusted to with relatively straightforward changes.

The easiest way to use this guide is to search for associated
error text.

## Dagster Types

There have been substantial changes to the core dagster type APIs.

Error:

`ImportError: cannot import name 'dagster_type' from 'dagster'`

Fix:

Use `usable_as_dagster_type` instead. If dynamically generating
types, construct using `DagsterType` instead.

Error:

`ImportError: cannot import name 'as_dagster_type' from 'dagster'`

Fix:

Use `make_python_type_usable_as_dagster_type` instead.

Further Information:

We have eliminated the `@dagster_type` and `as_dagster_type`
APIs, which previously were promoted as our primary type
creation API. This API automatically created a mapping
between a Python type and a Dagster Type. While convenient,
this ended up causing unpredictable behavior based on import
order, as well as being wholly incompatible with dynamically
created Dagster types.

Our core type creation API is now the `DagsterType` class. It creates a
Dagster type (which is just an instance of `DagsterType`) that can be passed
to `InputDefinition` and `OutputDefinition`.

The functionality of `@dagster_type` is preserved, but under a different name:
`usable_as_dagster_type`. This decorator signifies that the author wants
a bare Python type to be usable in contexts that expect dagster types, such as
an `InputDefinition` or `OutputDefinition`.

Any user that had been programatically creating dagster types and was forced
to decorate classes in local scope using `@dagster_type` and return that class
should instead just create a `DagsterType` directly.

`as_dagster_type` has replaced by `make_python_type_usable_as_dagster_type`.
The semantics of `as_dagster_type` did not indicate what is was actually doing
very well. This function is meant to take an _existing_ type -- often from
a library that one doesn't control -- and make that type usable as a dagster
type, the second argument.
