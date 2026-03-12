---
title: GCP Dataproc pipelines
description: 'Learn to integrate Dagster Pipes with GCP Dataproc to launch external code from Dagster assets.'
sidebar_position: 40
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

This article covers how to use [Dagster Pipes](/integrations/external-pipelines) to [submit jobs](https://cloud.google.com/dataproc/docs/guides/submit-job) to [GCP Dataproc](https://cloud.google.com/dataproc).

The [dagster-gcp](/integrations/libraries/gcp/dagster-gcp) integration library provides the <PyObject section="libraries" integration="gcp" module="dagster_gcp" object="pipes.PipesDataprocJobClient" /> resource, which can be used to launch GCP Dataproc jobs from Dagster assets and ops. Dagster can receive events such as logs, asset checks, or asset materializations from jobs launched with this client. The client requires minimal code changes to your Dataproc jobs.

## Prerequisites

To run the examples, you'll need to:

- Create a new Dagster project:
  <ScaffoldProject />
- Install the necessary Python libraries:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add 'dagster-gcp[dataproc]'
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install 'dagster-gcp[dataproc]'
         ```

   </TabItem>
</Tabs>

- Configure GCP authentication for applications. If you don't have this set up already, refer to the [GCP authentication guide](https://cloud.google.com/docs/authentication/gcloud)
- In GCP, you'll need:
  - An existing project with a Dataproc cluster.
  - Prepared infrastructure such as GCS buckets, IAM roles, and other resources required for your Dataproc job.

## Step 1: Install the dagster-pipes module in your Dataproc environment

Choose one of the [options](https://cloud.google.com/dataproc/docs/tutorials/python-configuration) to install `dagster-pipes` in the Dataproc environment.

For example, use the following property in your configuration:

```yaml
dataproc:pip.packages: 'dagster-pipes,google-cloud-storage'
```

`google-cloud-storage` is an optional dependency required for passing Pipes messages from the Dataproc job to Dagster.

## Step 2: Add dagster-pipes to the Dataproc job script

Call `open_dagster_pipes` in the Dataproc script to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/gcp/dataproc_job/script.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/integrations/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Create an asset using the PipesDataprocJobClient to launch the job

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In the Dagster asset/op code, use the `PipesDataprocJobClient` resource to launch the job:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/gcp/dataproc_job/dagster_code.py"
  startAfter="start_asset_marker"
  endBefore="end_asset_marker"
  title="src/<project_name>/defs/assets.py"
/>

This will launch the Dataproc job and wait for it to complete. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be terminated.

Setting `include_stdtio_in_messages=True` in the `PipesDataprocJobClient` constructor enables forwarding `stdout` and `stderr` from the job driver to Dagster.

## Step 4: Create Dagster definitions

Next, add the `PipesDataprocJobClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/gcp/dataproc_job/dagster_code.py"
  startAfter="start_definitions_marker"
  endBefore="end_definitions_marker"
  title="src/<project_name>/defs/resources.py"
/>

Dagster will now be able to launch the GCP Dataproc job from the `dataproc_asset` asset, and receive logs and events from the job.
