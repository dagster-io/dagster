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

## Config System

The config APIs have been renamed to have no collisions with names in neither python's
`typing` API nor the dagster type system. Here are some example errors:

Error:

`dagster.core.errors.DagsterInvariantViolationError: Cannot resolve Dagster Type Optional.Int to a config type. Repr of type: <dagster.core.types.dagster_type.OptionalType object at 0x102bb2a50>`

Fix:

Use `Noneable` of `Optional`.

Error:

`TypeError: 'DagsterDictApi' object is not callable`

Fix:

Pass a raw python dictionary instead of Dict.

`config=Dict({'foo': str})` becomes `config={'foo': str}`

Error:

`ImportError: cannot import name 'PermissiveDict' from 'dagster'`

Fix:

Use `Permissive` instead.

Error:

`dagster.core.errors.DagsterInvariantViolationError: Cannot use List in the context of config. Please use a python list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead.`

Fix:

This happens when a properly constructed List is used within config. Use Array instead.

Error:

`dagster.core.errors.DagsterInvalidDefinitionError: Invalid type: dagster_type must be DagsterType, a python scalar, or a python type that has been marked usable as a dagster type via @usable_dagster_type or make_python_type_usable_as_dagster_type: got <dagster.config.config_type.Noneable object at 0x1029c8a10>.`

Fix:

This happens when a List takes an invalid argument and is never constructed.
The error could be much better. This is what happens a config type (in this
case `Noneable`) is passed to a `List`. The fix is to use either `Array` or
to use a bare list with a single element, which is a config type.

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

## Scheduler

Scheduler configuration has been moved to the `dagster.yaml`. After upgrading, the previous schedule
history is no longer compatible with the new storage.

Make sure you delete your existing `$DAGSTER_HOME/schedules` directory, then run:

```
dagster schedule wipe && dagster schedule up
```

Error:

`TypeError: schedules() got an unexpected keyword argument 'scheduler'`

Fix:

The `@schedules` decorator no longer takes a `scheduler` argument. Remove the argument and instead
configure the scheduler on the instance.

Instead of:

```
@schedules(scheduler=SystemCronScheduler)
def define_schedules():
    ...
```

Remove the `scheduler` argument:

```
@schedules
def define_schedules():
    ...
```

Configure the scheduler on your instance by adding the following to `$DAGSTER_HOME/dagster.yaml`:

```
scheduler:
    module: dagster_cron.cron_scheduler
    class: SystemCronScheduler
```

Error:

`TypeError: <lambda>() takes 0 positional arguments but 1 was given"`

Stack Trace:

```
    File ".../dagster/python_modules/dagster/dagster/core/definitions/schedule.py", line 171, in should_execute
        return self._should_execute(context)
```

Fix:

The `should_execute` and `environment_dict_fn` argument to `ScheduleDefinition` now has a required
first argument `context`, representing the `ScheduleExecutionContext`.
