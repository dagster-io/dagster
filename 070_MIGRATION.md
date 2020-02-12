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

Error:

`dagster.core.errors.DagsterInvalidDefinitionError: type_check_fn argument type "BadType" must take 2 arguments, received 1`

Fix:

Add a context argument (named `_`, `_context`, `context`, or `context_`) as the first argument
of the `type_check_fn`. The second argument is the value being type-checked.

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

The `type_check_fn` argument has been renamed from `type_check` and now takes
two arguments instead of one. The first argument is a instance of `TypeCheckContext`;
the second argument is the value being checked. This allows the type check
to have access to resources.

## Required Resources

Any solid, type, or configuration function that accesses a resource off of a context
object must declare that resource key with a `required_resource_key` argument.

Error:

`DagsterUnknownResourceError: Unknown resource <resource_name>. Specify <resource_name> as a required resource on the compute / config function that accessed it.`

Fix:

Find any references to `context.resources.<resource_name>`, and ensure that the enclosing
solid definition, type definition, or config function has the resource key specified
in its `required_resource_key` argument.

Further information:

When only a subset of solids are being executed in a given process, we only need to
initialize resources that will be used by that subset of solids. In order to improve
the performance of pipeline execution, we need each solid and type to explicitly declare
its required resources.

As a result, we should see improved performance for pipeline subset execution,
multiprocess execution, and retry execution.

## RunConfig Removed

Error:

`AttributeError: 'ComputeExecutionContext' object has no attribute 'run_config'`

Fix:

Replace all references to `context.run_config` with `context.pipeline_run`. The `run_config` field
on the pipeline execution context has been removed and replaced with `pipeline_run`, a `PipelineRun`
instance. Along with the fields previously on `RunConfig`, this also includes the pipeline run
status.
