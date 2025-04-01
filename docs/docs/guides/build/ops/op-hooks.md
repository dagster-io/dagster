---
title: 'Op hooks'
description: Op hooks let you define success and failure handling policies on ops.
sidebar_position: 200
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

Op hooks let you define success and failure handling policies on ops.

## Relevant APIs

| Name                                                          | Description                                                                                                                |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="hooks" module="dagster" object="failure_hook" decorator /> | The decorator to define a callback on op failure.                                                                          |
| <PyObject section="hooks" module="dagster" object="success_hook" decorator /> | The decorator to define a callback on op success.                                                                          |
| <PyObject section="hooks" module="dagster" object="HookContext"  />           | The context object available to a hook function.                                                                           |
| <PyObject section="hooks" module="dagster" object="build_hook_context" />     | A function for building a <PyObject section="hooks" module="dagster" object="HookContext" /> outside of execution, intended to be used when testing a hook. |

## Overview

A <PyObject section="hooks" module="dagster" object="success_hook" decorator /> or <PyObject section="hooks" module="dagster" object="failure_hook" decorator /> decorated function is called an op hook. Op hooks are designed for generic purposes — it can be anything you would like to do at a per op level.

## Defining an op hook

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_repo_marker_0" endBefore="end_repo_marker_0" />

### Hook context

As you may have noticed, the hook function takes one argument, which is an instance of <PyObject section="hooks" module="dagster" object="HookContext" />. The available properties on this context are:

- `context.job_name`: the name of the job where the hook is triggered.
- `context.log`: loggers
- `context.hook_def`: the hook that the context object belongs to.
- `context.op`: the op associated with the hook.
- `context.op_config`: The config specific to the associated op.
- `context.op_exception`: The thrown exception in the associated failed op.
- `context.op_output_values`: The computed output values of the associated op.
- `context.step_key`: the key for the step where the hook is triggered.
- `context.resources`: the resources the hook can use.
- `context.required_resource_keys`: the resources required by this hook.

## Using hooks

Dagster provides different ways to trigger op hooks.

### Applying a hook on every op in a job

For example, you want to send a slack message to a channel when any op fails in a job. In this case, we will be applying a hook on a job, which will apply the hook on every op instance within in that job.

The <PyObject section="jobs" module="dagster" object="job" decorator /> decorator accepts `hooks` as a parameter. Likewise, when creating a job from a graph, hooks are also accepted as a parameter in the <PyObject section="graphs" module="dagster" object="GraphDefinition.to_job" /> function. In the below example, we can pass the `slack_message_on_failure` hook above in a set as a parameter to <PyObject section="jobs" module="dagster" object="job" decorator />. Then, slack messages will be sent when any op in the job fails.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_repo_marker_1" endBefore="end_repo_marker_1" />

When you run this job, you can provide configuration to the slack resource in the run config:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/prod_op_hooks.yaml" />

or by using the [configured API](/api/python-api/config#dagster.configured):

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_repo_marker_1_with_configured" endBefore="end_repo_marker_1_with_configured" />

### Applying a hook on an op

Sometimes a job is a shared responsibility or you only want to be alerted on high-priority op executions. So we also provide a way to set up hooks on op instances which enables you to apply policies on a per-op basis.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_repo_marker_2" endBefore="end_repo_marker_2" />

In this case, op "b" won't trigger any hooks, while when op "a" fails or succeeds it will send a slack message.

## Testing hooks

You can test the functionality of a hook by invoking the hook definition. This will run the underlying decorated function. You can construct a context to provide to the invocation using the <PyObject section="hooks" module="dagster" object="build_hook_context" /> function.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_testing_hooks" endBefore="end_testing_hooks" />

## Examples

### Accessing failure information in a failure hook

In many cases, you might want to know details about an op failure. You can get the exception object thrown in the failed op via the `op_exception` property on <PyObject section="hooks" module="dagster" object="HookContext" />:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks_context.py" startAfter="start_failure_hook_op_exception" endBefore="end_failure_hook_op_exception" />

## Patterns

### Environment-specific hooks using jobs

Hooks use resource keys to access resources. After including the resource key in its set of `required_resource_keys`, the body of the hook can access the corresponding resource via the `resources` attribute of its context object.

It also enables you to switch resource values in different jobs so that, for example, you can send slack messages only while executing a production job and mock the slack resource while testing.

Because executing a production job and a testing job share the same core of business logic, we can build these jobs from a shared [graph](/guides/build/jobs/op-jobs#from-a-graph). In the <PyObject section="graphs" module="dagster" object="GraphDefinition.to_job" /> method, which builds a job from a graph, you can specify environment-specific hooks and resources.

In this case, we can mock the `slack_resource` using a helper function <PyObject section="resources" module="dagster" object="ResourceDefinition" displayText="ResourceDefinition.hardcoded_resource()"/>, so it won't send slack messages during development.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_repo_marker_3" endBefore="end_repo_marker_3" />

When we switch to production, we can provide the real slack token in the `run_config` and therefore enable sending messages to a certain slack channel when a hook is triggered.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/prod_op_hooks.yaml" />

Then, we can execute a job with the config through Python API, CLI, or the Dagster UI. Here's an example of using the Python API.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/op_hooks.py" startAfter="start_repo_main" endBefore="end_repo_main" />

### Job-level hooks

When you add a hook to a job, the hook will be added to every op in the job individually. The hook does not track job-scoped events and only tracks op-level success or failure events.

You may find the need to set up job-level policies. For example, you may want to run some code for every job failure.

Dagster provides a way to create a sensor that reacts to job failure events. You can find detail in the [Sensors docs](/guides/automate/sensors/).