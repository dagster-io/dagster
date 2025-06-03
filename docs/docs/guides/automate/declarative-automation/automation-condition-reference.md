---
description: Operands and operators that you can use to customize Dagster Declarative Automation conditions.
sidebar_position: 400
title: Automation condition reference
---

## Operands

Operands are base conditions which can be true or false about a given target. For partitioned assets, the target will be a given partition of the asset.

| Operand                                     | Description                                                                                                                                                |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AutomationCondition.missing`               | Target has not been executed                                                                                                                               |
| `AutomationCondition.in_progress`           | Target is part of an in-progress run                                                                                                                       |
| `AutomationCondition.execution_failed`      | Target failed to be executed in its latest run                                                                                                             |
| `AutomationCondition.newly_updated`         | Target was updated since the previous evaluation                                                                                                           |
| `AutomationCondition.newly_requested`       | Target was requested on the previous evaluation                                                                                                            |
| `AutomationCondition.code_version_changed`  | Target has a new code version since the previous evaluation                                                                                                |
| `AutomationCondition.cron_tick_passed`      | A new tick of the provided cron schedule occurred since the previous evaluation                                                                            |
| `AutomationCondition.in_latest_time_window` | Target falls within the latest time window of the asset’s <PyObject section="partitions" module="dagster" object="PartitionsDefinition" />, if applicable. |
| `AutomationCondition.will_be_requested`     | Target will be requested in this tick                                                                                                                      |
| `AutomationCondition.initial_evaluation`    | This is the first evaluation of this condition                                                                                                             |

## Operators

The [operands](#operands) can be built into more complex expressions using the following operators:

<table
  className="table"
  style={{
    width: '100%',
  }}>
  <thead>
    <tr>
      <th
        style={{
          width: '40%',
        }}>
        Operator
      </th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <code>~</code> (tilde)
      </td>
      <td>
        NOT; condition is not true; ex: <code>~A</code>
      </td>
    </tr>
    <tr>
      <td>
        <code>|</code> (pipe)
      </td>
      <td>
        OR; either condition is true; ex: <code>A | B</code>
      </td>
    </tr>
    <tr>
      <td>
        <code>&</code> (ampersand)
      </td>
      <td>
        AND; both conditions are true; ex: <code>A & B</code>
      </td>
    </tr>
    <tr>
      <td>
        <code>A.newly_true()</code>
      </td>
      <td>Condition A was false on the previous evaluation and is now true.</td>
    </tr>
    <tr>
      <td>
        <code>A.since(B)</code>
      </td>
      <td>Condition A became true more recently than Condition B.</td>
    </tr>
    <tr>
      <td>
        <code>AutomationCondition.any_deps_match(A)</code>
      </td>
      <td>
        Condition A is true for any upstream partition. Can be used with <code>.allow()</code> and{' '}
        <code>.ignore()</code> to target specific upstream assets.
      </td>
    </tr>
    <tr>
      <td>
        <code>AutomationCondition.all_deps_match(A)</code>
      </td>
      <td>
        Condition A is true for at least one partition of each upstream asset. Can be used with <code>.allow()</code>{' '}
        and <code>.ignore()</code> to target specific upstream assets.
      </td>
    </tr>
    <tr>
      <td>
        <code>AutomationCondition.any_downstream_conditions()</code>
      </td>
      <td>
        Any <PyObject section="assets" module="dagster" object="AutomationCondition" /> on a downstream asset evaluates
        to true.
      </td>
    </tr>
  </tbody>
</table>

## Composite conditions

There are a set of pre-built conditions that make it easier to construct common combinations of the above conditions.

| Condition                                         | Description                                                                            |
| ------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `AutomationCondition.any_deps_updated`            | Any dependencies have been updated since the previous evaluation                       |
| `AutomationCondition.any_deps_missing`            | Any dependencies have never been materialized or observed                              |
| `AutomationCondition.any_deps_in_progress`        | Any dependencies are part of an in-progress run                                        |
| `AutomationCondition.all_deps_updated_since_cron` | All dependencies have been updated since the latest tick of the provided cron schedule |

## Evaluations

Evaluation of each automation condition is handled by an <PyObject section="assets" module="dagster" object="AutomationConditionSensorDefinition" />. By default, a sensor with the name `default_automation_condition_sensor` will be available in all code locations that have at least one asset with an `AutomationCondition`. This sensor will evaluate all available conditions every 30 seconds, and launch runs for any conditions that evaluate to true at that time.

Because evaluations happen at discrete times, and not continuously, this means that many of the above conditions are defined in relation to these evaluation ticks. For example, `AutomationCondition.cron_tick_passed()` becomes true on the first evaluation after a cron schedule tick is passed.

## Statuses and events

There are two general categories of `AutomationConditions`:

- **Statuses** are persistent states that are and will be true for some period of time. For example, the `AutomationCondition.missing()` condition will be true only if an asset partition has never been materialized or observed.

- **Events** are transient and reflect something that may only be true for an instant. For example, the `AutomationCondition.newly_updated()` condition will be true only if an asset partition was materialized since the previous evaluation.

Using the `<A>.since(<B>)` operator, you can create conditions that detect if one event has happened more recently than another. Think of this as converting two events to a status - in this case, `A has occurred more recently than B` - as this will stay true for some period of time. This operator becomes true whenever `<A>` is true, and will remain true until `<B>` is also true. Conversely, it can also be useful to convert statuses to events. For example, the default `eager()` condition ensures that Dagster only tries to materialize a missing asset partition once using the following sub-condition:

```python
import dagster as dg

dg.AutomationCondition.missing().newly_true().since_last_handled()
```

By using the `<A>.newly_true()` operator, you can turn the status of _"being missing"_ into a single event, specifically the point in time where an asset partition entered the _missing_ state. This is done because an asset partition will generally remain missing for several evaluations after a run is initially requested, as that run spins up and does the work required to materialize the asset. To avoid continually requesting partitions during this time, this condition is designed to only be true from the point in time that the partition becomes missing to the point in time that we request a run to materialize it. After that point in time, the event is considered to be "handled", and the subcondition will remain false.

## Run grouping

AutomationConditions generally depend on the status of their dependencies. For example, `AutomationCondition.eager()` executes after a dependency updates, and `AutomationCondition.on_cron()` only executes after all dependencies have updated since a given cron schedule tick.

However, when you have multiple assets in a sequence, all with conditions which depend on the state of their dependencies, it would be inconvenient for each asset in that sequence to be executed in its own independent run. Ideally, if you have multiple eager assets in a chain, an update to the first would create a single run that targets all downstream assets, even though the dependencies of those assets haven't technically updated yet. The intuition here is that if we know we plan to update an asset on this evaluation, then downstream assets can treat that the same as if the asset already did update.

This handling is included automatically in the composite conditions `AutomationCondition.any_deps_updated()` and `AutomationCondition.any_deps_missing()`, which both rely on `AutomationCondition.will_be_requested()` to find asset partitions that will be executed on this tick, and can be grouped into the same run as the currently-evaluated asset.
