---
title: "Executing code outside of Dagster with Pipes"
sidebar_position: 40
sidebar_label: "External execution with Pipes"
---

# Executing code outside of Dagster with Pipes

Dagster Pipes provides a powerful mechanism for invoking code outside of Dagster, while providing all the benefits of scheduling, reporting, and observability of native Dagster pipelines.

In this guide, we'll walk you through how to invoke non-Dagster code through Pipes.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
</details>

## Setting up an asset that invokes your external code

To set up invoking code outside of Dagster, you first need to set up an asset.  We can invoke the external code within the asset function by using a Dagster Pipes client resource.

It's not a requirement that this external code know anything about Dagster.  It can even be a process running a different language on a remote machine - the only requirement is that it can be triggered from Python.

In the following example, our external code is in a Python script that we invoke within a Dagster asset.

<CodeExample filePath="guides/external-systems/pipes/external_code_opaque.py" language="python" title="/usr/bin/external_code.py" />
<CodeExample filePath="guides/external-systems/pipes/asset_wrapper.py" language="python" title="Asset invoking external compute using Dagster Pipes" />

Materializing this asset in Dagster from the UI or from a sensor/schedule will kick off the execution of that external code.

## Sending logs and metadata back to Dagster from external code

Dagster Pipes also establishes a protocol for external code to optionally send back log and metadata back to Dagster.  A Python client for this protocol is available as part of the `dagster_pipes` package.  To send back log and metadata back to Dagster, we can create a `PipesContext` object within our external code:

<CodeExample filePath="guides/external-systems/pipes/external_code_data_passing.py" language="python" title="/usr/bin/external_code.py" />

The logs sent back using the `PipesContext` will be visible in the structured logs of that asset materialization's run, and the materialization metadata will be reflected in the asset history.
