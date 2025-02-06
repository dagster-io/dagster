---
title: "Using Dagster pipes"
description: "Learn how to use Dagster Pipes's built-in subprocess implementation to invoke a subprocess with a given command and environment"
sidebar_position: 10
---

In this guide, we’ll show you how to use [Dagster Pipes](/guides/build/external-pipelines/) with Dagster’s built-in subprocess <PyObject section="pipes" module="dagster" object="PipesSubprocessClient" /> to run a local subprocess with a given command and environment. You can then send information such as structured metadata and logging back to Dagster from the subprocess, where it will be visible in the Dagster UI.

To get there, you'll:

- [Create a Dagster asset that invokes a subprocess](create-subprocess-asset)
- [Modify existing code to work with Dagster Pipes to send information back to Dagster](modify-external-code)
- Learn about using Dagster Pipes with other entities in the Dagster system in the [Reference](reference) section

:::note

This guide focuses on using an out-of-the-box <PyObject section="pipes" module="dagster" object="PipesSubprocessClient" /> resource. For further customization with the subprocess invocation, use <PyObject section="libraries" module="dagster_pipes" object="open_dagster_pipes"/> approach instead. Refer to [Customizing Dagster Pipes protocols](/guides/build/external-pipelines/dagster-pipes-details-and-customization) for more info.

:::

## Prerequisites

To use Dagster Pipes to run a subprocess, you’ll need to have Dagster (`dagster`) and the Dagster UI (`dagster-webserver`) installed. Refer to the [Installation guide](/getting-started/installation) for more info.

You'll also need **an existing Python script.** We’ll use the following Python script to demonstrate. This file will be invoked by the Dagster asset that you’ll create later in this tutorial.

Create a file named `external_code.py` and paste the following into it:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/part_1/external_code.py" lineStart="3" />

## Ready to get started?

When you've fulfilled all the prerequisites for the tutorial, you can get started by [creating a Dagster asset that executes a subprocess](create-subprocess-asset).
