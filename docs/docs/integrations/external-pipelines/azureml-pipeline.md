---
title: Azure Machine Learning pipelines
description: 'Learn to integrate Dagster Pipes with Azure Machine Learning to launch external code from Dagster assets.'
sidebar_position: 35
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

This article covers how to use [Dagster Pipes](/integrations/external-pipelines) to submit jobs to [Azure Machine Learning](https://azure.microsoft.com/en-us/products/machine-learning).

The [dagster-azure](/integrations/libraries/azure/dagster-azure) integration library provides the `PipesAzureMLClient` resource, which can be used to launch Azure ML jobs from Dagster assets and ops. Dagster can receive events such as logs, asset checks, or asset materializations from jobs launched with this client. The client requires minimal code changes to your Azure ML jobs.

## Prerequisites

To run the examples, you'll need to:

- Create a new Dagster project:
  <ScaffoldProject />
- Install the necessary Python libraries:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster-azure
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster-azure
         ```

   </TabItem>
</Tabs>

- In Azure, you'll need:
  - An existing Azure ML workspace
  - An Azure Blob Data Storage Container to be used by Dagster. The recommended way to work with `dagster-pipes` and Azure ML is to use Azure Blob Data Storage to communicate between the Dagster orchestrator and the Azure ML job.

## Step 1: Create an Azure ML environment for Dagster Pipes

Your Azure ML job will require an Azure ML environment that contains the `dagster-pipes` library. Since the Azure ML job will be communicating with the Dagster orchestrator via Azure Blob Storage, we will also need to install the `azure-identity` and `azure-storage-blob` Python libraries.

In your Azure ML dashboard, choose "Add a Custom Environment", select the environment source you want to use (e.g. `sklearn-1.5:33`), and edit the list of Python packages to install.

For instance, if specifying Python dependencies using a `conda.yaml` file, include the following lines:

```yaml
dependencies:
  - python=3.10
  - pip:
      - dagster-pipes
      - azure-storage-blob
      - azure-identity
```

## Step 2: Add dagster-pipes to the Azure ML job script

Call `open_dagster_pipes` in your Azure ML script to create a context that can be used to send messages to Dagster:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/azure/azureml_job/train.py"
  title="train.py"
/>

:::info

Make sure that the identity that is configured for running Azure ML jobs has access to Dagster's Azure Blob Storage account.

:::

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/integrations/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 3: Create an asset using the PipesAzureMLClient to launch the job

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In the Dagster asset/op code, use the `PipesAzureMLClient` resource to launch the job:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/azure/azureml_job/dagster_code.py"
  startAfter="start_asset_marker"
  endBefore="end_asset_marker"
  title="src/<project_name>/defs/assets.py"
/>

This will launch the Azure ML job and wait for it to complete. If the job fails, the Dagster process will raise an exception. If the Dagster process is interrupted while the job is still running, the job will be canceled, provided that `forward_termination=True` is set in the client.

## Step 4: Create Dagster definitions

Next, add the `PipesAzureMLClient` resource to your project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/azure/azureml_job/dagster_code.py"
  startAfter="start_definitions_marker"
  endBefore="end_definitions_marker"
  title="src/<project_name>/defs/assets.py"
/>

Dagster will now be able to launch the Azure ML job from the `azureml_training_job` asset, and receive logs and events from the job.
