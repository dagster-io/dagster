---
title: Using resources in schedules
sidebar_position: 500
---

This example demonstrates how to use resources in schedules. To specify a resource dependency, annotate the resource as a parameter to the schedule's function.

:::note

This article assumes familiarity with [resources](/guides/build/external-resources/), [code locations and definitions](/guides/deploy/code-locations/), and [schedule testing](testing-schedules).

All Dagster definitions, including schedules and resources, must be attached to a <PyObject section="definitions" module="dagster" object="Definitions" /> call.

:::

{/* TODO add dedent=4 prop to CodeExample below when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_on_schedule" endBefore="end_new_resource_on_schedule" />

## APIs in this guide

| Name | Description |
|------|-------------|
| <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator /> | Decorator that defines a schedule that executes according to a given cron schedule. |
| <PyObject section="resources" module="dagster" object="ConfigurableResource" /> | |
| <PyObject section="jobs" module="dagster" object="job" decorator /> | The decorator used to define a job. |
| <PyObject section="schedules-sensors" module="dagster" object="RunRequest" />                          | A class that represents all the information required to launch a single run. |
| <PyObject section="config" module="dagster" object="RunConfig" /> | |
| <PyObject section="definitions" module="dagster" object="Definitions" /> | |
