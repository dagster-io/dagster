# Declarative Scheduling

_Note: This serves as a checked-in reference to be updated as the stack progresses. Eventually, this should be ported over to actual docs_

A core function of an orchestrator is scheduling: deciding if and when computations should run. In Dagster, scheduling an asset is accomplished by attaching a `SchedulingCondition` to its definition. This condition describes all situations in which an asset should be automatically kicked off.

## Built-in SchedulingConditions

Dagster provides an array of built-in `SchedulingConditions` which describe common states that an asset may be in. They are:

[to be implemented]

- `SchedulingCondition.materialized()`
- `SchedulingCondition.materialized_since_cron()`
- `SchedulingCondition.in_progress()`
- `SchedulingCondition.failed()`
- `SchedulingCondition.in_latest_time_window()`
- `SchedulingCondition.in_recent_time_window()`

These conditions may be combined in a variety of ways. All conditions support the boolean operators:

- `a | b`: Either `a` or `b`
- `a & b`: Both `a` and `b`
- `~a`: Not `a`

Conditions can also be applied to dependencies:

- `SchedulingCondition.any_deps_match(a)`: Any asset partition of any deps match condition `a`
- `SchedulingCondition.all_deps_match(a)`: Any asset partition of all deps match condition `a`

## Examples

[to be implemented]
